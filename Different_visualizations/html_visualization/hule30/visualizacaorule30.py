import numpy as np
from flask import Flask, render_template_string, jsonify
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class Rule30Model:
    def __init__(self, width=128):
        self.width = width
        self.state = 1 << (width // 2)
        self.steps = []
        self.collect_state()

    def step(self):
        next_state = 0
        for j in range(self.width):
            left = (self.state >> (j + 1)) & 1
            center = (self.state >> j) & 1
            right = (self.state >> (j - 1)) & 1 if j > 0 else 0
            next_state |= ((left ^ (center | right)) << j)
        self.state = next_state
        self.collect_state()

    def collect_state(self):
        row = [(self.state >> j) & 1 for j in range(self.width - 1, -1, -1)]
        self.steps.append(row)

app = Flask(__name__)
model = Rule30Model(width=128) 
max_steps = 64  
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
    ax.imshow(model.steps, cmap='binary', aspect='auto')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title("Rule 30 - Current State")
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    plt.close(fig)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Rule 30 Visualization</title>
  </head>
  <body>
    <div style="text-align: center;">
      <h1>Rule 30 Cellular Automaton</h1>
      <img id="rule30-image" src="data:image/png;base64,{{ plot_png }}" alt="Rule 30">
      <br><br>
      <button onclick="nextStep()">Next Step</button>
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
      function updateImage() {
        fetch('/plot.png').then(response => response.text()).then(data => {
          document.getElementById('rule30-image').src = 'data:image/png;base64,' + data;
        });
      }
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
