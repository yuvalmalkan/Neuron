import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  }

  /* Drag bar */
  #titlebar {
    -webkit-app-region: drag;
    height: 40px;
    width: 100%;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 999;
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 8px;
  }

  .dot {
    -webkit-app-region: no-drag;
    width: 12px; height: 12px;
    border-radius: 50%;
    cursor: pointer;
  }
  .dot.red    { background: #ff5f57; }
  .dot.yellow { background: #febc2e; }
  .dot.green  { background: #28c840; }

  /* Main layout */
  .app {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: 20px;
    padding: 60px 40px 40px;
  }

  /* Glass card */
  .glass-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04));
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    padding: 32px;
    width: 100%;
    max-width: 480px;
  }

  h1 {
    color: white;
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 24px;
    letter-spacing: -0.3px;
  }

  /* Glass input */
  .glass-input {
    width: 100%;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    padding: 12px 16px;
    color: white;
    font-size: 14px;
    outline: none;
    margin-bottom: 14px;
    transition: border 0.2s, background 0.2s;
    font-family: inherit;
  }

  .glass-input::placeholder { color: rgba(255,255,255,0.4); }

  .glass-input:focus {
    border-color: rgba(255,255,255,0.45);
    background: rgba(255,255,255,0.13);
  }

  /* Glass button */
  .glass-btn {
    width: 100%;
    padding: 13px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.25);
    background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06));
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: white;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: inherit;
    margin-top: 4px;
  }

  .glass-btn:hover {
    background: linear-gradient(135deg, rgba(255,255,255,0.26), rgba(255,255,255,0.12));
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }

  .glass-btn:active {
    transform: translateY(0px);
  }

  .glass-btn.secondary {
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.12);
    font-size: 13px;
    padding: 10px;
  }

  .label {
    color: rgba(255,255,255,0.5);
    font-size: 12px;
    margin-bottom: 6px;
    margin-top: 4px;
  }
</style>
</head>
<body>

<div id="titlebar">
  <div class="dot red"    onclick="pybridge.close()"></div>
  <div class="dot yellow" onclick="pybridge.minimize()"></div>
  <div class="dot green"></div>
</div>

<div class="app">
  <div class="glass-card">
    <h1>Neuron</h1>

    <div class="label">Target</div>
    <input class="glass-input" type="text" placeholder="IP / Domain / Username...">

    <div class="label">Mode</div>
    <input class="glass-input" type="text" placeholder="OSINT / Network Scan">

    <button class="glass-btn" onclick="this.textContent='Scanning...'">Run Scan</button>
    <button class="glass-btn secondary" style="margin-top:10px">Clear</button>
  </div>
</div>

</body>
</html>
"""

class NeuronApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(600, 500)
        self.center()

        self.browser = QWebEngineView(self)
        self.browser.setHtml(HTML)
        self.setCentralWidget(self.browser)

        self._drag_pos = None

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 600) // 2
        y = (screen.height() - 500) // 2
        self.move(x, y)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = NeuronApp()
    win.show()
    sys.exit(app.exec())