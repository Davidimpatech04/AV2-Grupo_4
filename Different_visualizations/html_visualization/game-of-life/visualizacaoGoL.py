import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d
from flask import Flask, render_template_string, jsonify, request
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class GameOfLifeModel(Model):
    def __init__(self, width=10, height=10, alive_fraction=0.2):
        super().__init__()
        self.cell_layer = PropertyLayer("cells", width, height, False, dtype=bool)
        self.cell_layer.data = np.random.choice([True, False], size=(width, height), p=[alive_fraction, 1 - alive_fraction])
        self.cell_layer_copy = np.copy(self.cell_layer.data) # guardar os dados iniciais
        self.cells = width * height
        self.alive_count = 0
        self.alive_fraction = 0
        self.datacollector = DataCollector(
            model_reporters={"Cells alive": "alive_count",
                             "Fraction alive": "alive_fraction"}
        )
        self.datacollector.collect(self)

    def step(self):
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]])

        neighbor_count = convolve2d(self.cell_layer.data, kernel, mode="same", boundary="wrap")

        self.cell_layer.data = np.logical_or(
            np.logical_and(self.cell_layer.data, np.logical_or(neighbor_count == 2, neighbor_count == 3)),
            np.logical_and(~self.cell_layer.data, neighbor_count == 3)
        )

        self.alive_count = np.sum(self.cell_layer.data)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)
    #Função resetar 
    def reset(self):
        self.cell_layer.data = self.cell_layer_copy
        self.alive_count = np.sum(self.cell_layer.data)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)

app = Flask(__name__)
model = GameOfLifeModel(width=20, height=20, alive_fraction=0.3)
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
    ax.imshow(model.cell_layer.data, cmap='binary')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title("Game of Life - Current State")
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    plt.close(fig)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')

@app.route('/start', methods=['POST'])
def start_new_game():
    global model, step_count
    width = int(request.json.get('width', 20))
    height = int(request.json.get('height', 20))
    alive_fraction = float(request.json.get('alive_fraction', 30)) / 100.0
    model = GameOfLifeModel(width=width, height=height, alive_fraction=alive_fraction)
    step_count = 0
    return jsonify(success=True)
@app.route('/reset')
def reset():
    model.reset()
    global step_count
    step_count = 0  
    return jsonify(success=True)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Game of Life Visualization</title>
  </head>
  <body>
    <div style="text-align: center;">
      <h1>Conway's Game of Life</h1>
      <img id="gol-image" src="data:image/png;base64,{{ plot_png }}" alt="Game of Life">
      <br><br>
      <input type="number" id="width" value="20" min="5" max="100">
      <input type="number" id="height" value="20" min="5" max="100">
      <input type="number" id="alive_fraction" value="30" min="0" max="100">
      <button onclick="startNewGame()">Start New Game</button>
      <br><br>
      <button onclick="nextStep()">Next Step</button>
      <button onclick="reset()">Reset</button>
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
      function reset() {
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

      function startNewGame() {
        const width = document.getElementById('width').value;
        const height = document.getElementById('height').value;
        const aliveFraction = document.getElementById('alive_fraction').value;
        
        fetch('/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            width: width,
            height: height,
            alive_fraction: aliveFraction
          })
        }).then(response => response.json()).then(data => {
          if (data.success) {
            updateImage(); // Atualiza a imagem após iniciar o novo jogo
          } else {
            alert('Error starting new game');
          }
        });
      }
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
