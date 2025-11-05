import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from World import World
from Vector import Vector
from Particle import Particle
from Composite import Composite
from Constraint import Constraint
from Material import Material


class MyGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.main_window.mouse_press(scene_pos.x(), scene_pos.y())

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        self.main_window.mouse_move(scene_pos.x(), scene_pos.y())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.main_window.mouse_release(scene_pos.x(), scene_pos.y())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soft Body Physics Editor")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create graphics scene and view
        self.scene = QGraphicsScene(self)
        self.view = MyGraphicsView(self)
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.view)

        # Initialize world
        self.world = World(Vector(800, 600))
        self.initialize_world()

        # Set up timer for simulation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // 60)  # 60 FPS

        # Mouse state
        self.selected_particle = None
        self.is_dragging = False

    def initialize_world(self):
        # Create a simple square for testing
        particles = []
        for i in range(4):
            x = 400 + 50 * (-1 if i % 2 == 0 else 1)
            y = 300 + 50 * (-1 if i < 2 else 1)
            particle = Particle(Vector(x, y), 1.0)
            particles.append(particle)
            self.world.AddParticle(particle)

        # Add constraints
        for i in range(4):
            self.world.AddConstraint(Constraint(particles[i], particles[(i+1)%4], 100.0, 0.99))
        self.world.AddConstraint(Constraint(particles[0], particles[2], 141.42, 0.99))
        self.world.AddConstraint(Constraint(particles[1], particles[3], 141.42, 0.99))

    def update_simulation(self):
        try:
            self.world.Simulate()
            self.render_scene()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.timer.stop()
            self.close()

    def render_scene(self):
        self.scene.clear()

        # Draw particles
        for particle in self.world.particles:
            color = QColor(255, 0, 0)
            brush = QBrush(color)
            self.scene.addEllipse(particle.position.x - 5, particle.position.y - 5, 10, 10, QPen(), brush)

        # Draw constraints
        for constraint in self.world.constraints:
            color = QColor(0, 0, 255)
            pen = QPen(color)
            self.scene.addLine(constraint.particleA.position.x, constraint.particleA.position.y,
                               constraint.particleB.position.x, constraint.particleB.position.y, pen)

    def mouse_press(self, x, y):
        # Find the closest particle to the mouse position
        closest_particle = None
        min_distance = float('inf')
        for particle in self.world.particles:
            distance = Vector(x, y).distance(particle.position)
            if distance < 10 and distance < min_distance:
                closest_particle = particle
                min_distance = distance
        if closest_particle:
            self.selected_particle = closest_particle
            self.is_dragging = True

    def mouse_move(self, x, y):
        if self.is_dragging and self.selected_particle:
            self.selected_particle.position = Vector(x, y)
            self.selected_particle.previous_position = Vector(x, y)  # Prevent spring back

    def mouse_release(self, x, y):
        self.is_dragging = False
        self.selected_particle = None


if __name__ == "__main__":
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("Creating main window...")
        window = MainWindow()
        print("Showing main window...")
        window.show()
        print("Entering event loop...")
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")