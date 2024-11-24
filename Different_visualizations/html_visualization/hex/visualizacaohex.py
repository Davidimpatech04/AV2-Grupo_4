import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from flask import Flask, render_template_string, jsonify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import threading
import time
from matplotlib.patches import RegularPolygon

class HexGameOfLifeModel(Model):
    def __init__(self, width=10, height=10, alive_fraction=0.2):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = np.random.choice([True, False], size=(width, height), p=[alive_fraction, 1 - alive_fraction])
        self.grid_copy = np.copy(self.grid) #Salvar configuração inicial
        self.cells = width * height
        self.alive_count = 0
        self.alive_fraction = 0
        self.datacollector = DataCollector(
            model_reporters={"Cells alive": "alive_count",
                             "Fraction alive": "alive_fraction"}
        )
        self.datacollector.collect(self)

    def step(self):
        new_grid = np.copy(self.grid)
        for x in range(self.width):
            for y in range(self.height):
                neighbors = self.count_neighbors(x, y)
                if self.grid[x, y]:
                    if neighbors < 2 or neighbors > 3:
                        new_grid[x, y] = False
                else:
                    if neighbors == 3:
                        new_grid[x, y] = True
        
        self.grid = new_grid
        self.alive_count = np.sum(self.grid)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)
    #função reset 
    def reset(self):
        self.grid = self.grid_copy 
        self.alived_count = 0
        self.alived_fraction = 0
        self.datacollector.collect(self)
        

    def count_neighbors(self, x, y):
        directions = [
            (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)  # Hexagonal neighbors
        ]
        count = 0
        for dx, dy in directions:
            nx, ny = (x + dx) % self.width, (y + dy) % self.height
            if self.grid[nx, ny]:
                count += 1
        return count

app = Flask(__name__)
model = HexGameOfLifeModel(width=20, height=20, alive_fraction=0.3)
max_steps = 100
step_count = 0

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, plot_png=plot_png())

@app.route('/step')
def step():
    global step_count
    if step_count < max_steps:
        model.step()
        step_count += 1
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Maximum number of steps reached.")

@app.route('/plot.png')
def plot_png():
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-1, model.width + 1)
    ax.set_ylim(-1, model.height * np.sqrt(3) / 2 + 1)
    ax.set_anchor('C')  # Center the grid within the box

    for x in range(model.width):
        for y in range(model.height):
            hex_x = x + 0.5 * (y % 2)
            hex_y = y * np.sqrt(3) / 2
            color = 'black' if model.grid[x, y] else 'white'
            hexagon = RegularPolygon((hex_x, hex_y), numVertices=6, radius=0.5 * 0.95, 
                                     orientation=np.radians(30), facecolor=color, edgecolor='gray')
            ax.add_patch(hexagon)

    ax.set_xticks([])
    ax.set_yticks([])
    plt.axis('off')  # Turn off the axis for better centering
    plt.title("Hexagonal Game of Life - Current State", pad=20)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Adjust plot to center properly

    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    plt.close(fig)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')
@app.route('/reset')
#Chamando reset
def reset():
    global step_count
    model.reset()
    step_count = 0
    return jsonify(success=True)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Hexagonal Game of Life Visualization</title>
  </head>
  <body>
    <div style="text-align: center;">
      <h1>Hexagonal Game of Life</h1>
      <img id="gol-image" src="data:image/png;base64,{{ plot_png }}" alt="Hexagonal Game of Life">
      <br><br>
      <button onclick="nextStep()">Next Step</button>
      <button onclick="resetModel()">Reset</button>
    </div>
    <script>
      function nextStep() {
        fetch('/step').then(response => response.json()).then(data => {
          if (data.success) {
            updateImage();
          } else {
            alert(data.message);
          }
        });
      }
      function resetModel() {
        fetch('/reset').then(response => response.json()).then(data => {
          if (data.success) {
            updateImage(); // Atualiza a imagem após o reset
          }
        });
        }
      function updateImage() {
        fetch('/plot.png').then(response => response.text()).then(data => {
          document.getElementById('gol-image').src = 'data:image/png;base64,' + data;
        });
      }
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True, port=5000)
