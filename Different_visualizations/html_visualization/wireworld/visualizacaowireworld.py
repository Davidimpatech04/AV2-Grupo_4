import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from flask import Flask, render_template_string, jsonify, request
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import os
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import threading
import time


EMPTY = 0
ELECTRON_HEAD = 1
ELECTRON_TAIL = 2
CONDUCTOR = 3

class WireworldModel(Model):
    def __init__(self, width=10, height=10, initial_configuration=None):
        super().__init__()
        self.cell_layer = PropertyLayer("cells", width, height, False, dtype=int)
        if initial_configuration is None:
            self.cell_layer.data = np.full((width, height), EMPTY, dtype=int)
        else:
            self.cell_layer.data = np.array(initial_configuration)

        self.datacollector = DataCollector(
            model_reporters={"State": lambda m: m.cell_layer.data.copy()}
        )
        self.datacollector.collect(self)

    def step(self):
        new_data = self.cell_layer.data.copy()
        for x in range(self.cell_layer.data.shape[0]):
            for y in range(self.cell_layer.data.shape[1]):
                cell = self.cell_layer.data[x, y]
                if cell == ELECTRON_HEAD:
                    new_data[x, y] = ELECTRON_TAIL
                elif cell == ELECTRON_TAIL:
                    new_data[x, y] = CONDUCTOR
                elif cell == CONDUCTOR:
                    neighbors = [
                        self.cell_layer.data[(x + dx) % self.cell_layer.data.shape[0], (y + dy) % self.cell_layer.data.shape[1]]
                        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    ]
                    electron_head_count = neighbors.count(ELECTRON_HEAD)
                    if electron_head_count == 1 or electron_head_count == 2:
                        new_data[x, y] = ELECTRON_HEAD
        
        self.cell_layer.data = new_data
        self.datacollector.collect(self)

app = Flask(__name__)
model = WireworldModel(width=20, height=20)
max_steps = 100
step_count = 0

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, model=model)

@app.route('/toggle_cell', methods=['POST'])
def toggle_cell():
    data = request.json
    x, y = data['x'], data['y']
    current_state = model.cell_layer.data[x, y]
    if current_state == EMPTY:
        model.cell_layer.data[x, y] = CONDUCTOR
    elif current_state == CONDUCTOR:
        model.cell_layer.data[x, y] = ELECTRON_HEAD
    elif current_state == ELECTRON_HEAD:
        model.cell_layer.data[x, y] = ELECTRON_TAIL
    elif current_state == ELECTRON_TAIL:
        model.cell_layer.data[x, y] = EMPTY
    return jsonify(success=True)

@app.route('/step')
def step():
    global step_count
    if step_count < max_steps:
        model.step()
        step_count += 1
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Maximum number of steps reached.")

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Wireworld Visualization</title>
    <style>
      .grid-container {
        display: grid;
        grid-template-columns: repeat(20, 20px);
        grid-gap: 1px;
      }
      .cell {
        width: 20px;
        height: 20px;
        background-color: black;
      }
      .conductor {
        background-color: yellow;
      }
      .electron-head {
        background-color: blue;
      }
      .electron-tail {
        background-color: red;
      }
    </style>
  </head>
  <body>
    <div style="text-align: center;">
      <h1>Wireworld Simulation</h1>
      <div class="grid-container">
        {% for x in range(20) %}
          {% for y in range(20) %}
            <div class="cell {{ 'conductor' if model.cell_layer.data[x, y] == 3 else 'electron-head' if model.cell_layer.data[x, y] == 1 else 'electron-tail' if model.cell_layer.data[x, y] == 2 else '' }}" onclick="toggleCell({{ x }}, {{ y }})"></div>
          {% endfor %}
        {% endfor %}
      </div>
      <br><br>
      <button onclick="nextStep()">Run Simulation</button>
    </div>
    <script>
      function toggleCell(x, y) {
        fetch('/toggle_cell', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({x: x, y: y})
        }).then(response => response.json()).then(data => {
          if (data.success) {
            location.reload();
          } else {
            alert(data.message);
          }
        });
      }

      function nextStep() {
        fetch('/step').then(response => response.json()).then(data => {
          if (data.success) {
            location.reload();
          } else {
            alert(data.message);
          }
        });
      }
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
