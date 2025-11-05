# App3D.py
# Created by Michael Marek (2015)
# A 3D GUI application for soft-body physics simulation using PyQt6 and ModernGL.

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt6.QtCore import Qt
import moderngl
import numpy as np
from Vector import Vector
from World import World


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.ibo = None
        self.world = None
        self.mouse_pressed = False
        self.last_mouse_pos = Vector(0, 0)
        self.camera_pos = Vector(0, 0, 10)
        self.camera_yaw = 0
        self.camera_pitch = 0

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.clear_color = (0.1, 0.1, 0.15, 1.0)

        # Create shader program
        vertex_shader = """
        #version 330 core
        in vec3 in_vert;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 proj;
        void main() {
            gl_Position = proj * view * model * vec4(in_vert, 1.0);
        }
        """

        fragment_shader = """
        #version 330 core
        out vec4 fragColor;
        void main() {
            fragColor = vec4(0.8, 0.3, 0.3, 1.0);
        }
        """

        self.prog = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

        # Create world
        self.world = World(Vector(10, 10, 10), Vector(0, -9.8, 0))

        # Create a simple 3D cloth
        self.create_cloth()

    def create_cloth(self):
        # Create particles in a grid
        particles = []
        grid_size = 10
        spacing = 0.5
        for x in range(grid_size):
            for y in range(grid_size):
                particle = self.world.AddParticle(
                    x * spacing - (grid_size * spacing) / 2,
                    5,
                    y * spacing - (grid_size * spacing) / 2
                )
                # Pin top corners
                if x == 0 and y == 0 or x == grid_size - 1 and y == 0:
                    particle.material.mass = 0
                particles.append(particle)

        # Create constraints
        for x in range(grid_size):
            for y in range(grid_size):
                index = x * grid_size + y
                # Structural constraints (horizontal and vertical)
                if x < grid_size - 1:
                    self.world.AddConstraint(particles[index], particles[index + 1], 0.9)
                if y < grid_size - 1:
                    self.world.AddConstraint(particles[index], particles[index + grid_size], 0.9)
                # Shear constraints (diagonal)
                if x < grid_size - 1 and y < grid_size - 1:
                    self.world.AddConstraint(particles[index], particles[index + grid_size + 1], 0.9)
                    self.world.AddConstraint(particles[index + 1], particles[index + grid_size], 0.9)

    def paintGL(self):
        self.ctx.clear()

        # Simulate physics
        self.world.Simulate()

        # Render particles as spheres
        for particle in self.world.particles:
            self.render_sphere(particle.position, 0.05)

        # Render constraints as cylinders
        for constraint in self.world.constraints:
            self.render_cylinder(constraint.node1.position, constraint.node2.position, 0.02)

        self.ctx.finish()
        self.update()

    def render_sphere(self, pos, radius):
        # Simple sphere rendering using a quad
        # This is a placeholder - in a real app, you'd use a proper sphere mesh
        vertices = np.array([
            pos.x - radius, pos.y - radius, pos.z,
            pos.x + radius, pos.y - radius, pos.z,
            pos.x + radius, pos.y + radius, pos.z,
            pos.x - radius, pos.y + radius, pos.z,
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

        vbo = self.ctx.buffer(vertices.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())

        vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_vert')
        vao.index_buffer = ibo

        # Set uniforms
        self.prog['model'].value = np.identity(4, dtype=np.float32)
        self.prog['view'].value = self.get_view_matrix()
        self.prog['proj'].value = self.get_projection_matrix()

        vao.render(moderngl.TRIANGLES)

        vbo.release()
        ibo.release()
        vao.release()

    def render_cylinder(self, pos1, pos2, radius):
        # Simple cylinder rendering using a quad
        # This is a placeholder - in a real app, you'd use a proper cylinder mesh
        vertices = np.array([
            pos1.x - radius, pos1.y, pos1.z - radius,
            pos2.x - radius, pos2.y, pos2.z - radius,
            pos2.x + radius, pos2.y, pos2.z + radius,
            pos1.x + radius, pos1.y, pos1.z + radius,
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

        vbo = self.ctx.buffer(vertices.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())

        vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_vert')
        vao.index_buffer = ibo

        # Set uniforms
        self.prog['model'].value = np.identity(4, dtype=np.float32)
        self.prog['view'].value = self.get_view_matrix()
        self.prog['proj'].value = self.get_projection_matrix()

        vao.render(moderngl.TRIANGLES)

        vbo.release()
        ibo.release()
        vao.release()

    def get_view_matrix(self):
        # Simple camera view matrix
        yaw = np.radians(self.camera_yaw)
        pitch = np.radians(self.camera_pitch)

        # Rotation matrix
        rot_x = np.array([
            [1, 0, 0, 0],
            [0, np.cos(pitch), -np.sin(pitch), 0],
            [0, np.sin(pitch), np.cos(pitch), 0],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        rot_y = np.array([
            [np.cos(yaw), 0, np.sin(yaw), 0],
            [0, 1, 0, 0],
            [-np.sin(yaw), 0, np.cos(yaw), 0],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        rotation = np.dot(rot_y, rot_x)

        # Translation matrix
        translation = np.array([
            [1, 0, 0, -self.camera_pos.x],
            [0, 1, 0, -self.camera_pos.y],
            [0, 0, 1, -self.camera_pos.z],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        return np.dot(rotation, translation)

    def get_projection_matrix(self):
        # Perspective projection matrix
        fov = 45.0
        aspect = self.width() / self.height()
        near = 0.1
        far = 100.0

        f = 1.0 / np.tan(np.radians(fov) / 2.0)

        return np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0],
        ], dtype=np.float32)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = True
            self.last_mouse_pos = Vector(event.x(), event.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = False

    def mouseMoveEvent(self, event):
        if self.mouse_pressed:
            current_pos = Vector(event.x(), event.y())
            delta = current_pos - self.last_mouse_pos
            self.last_mouse_pos = current_pos

            # Update camera rotation
            self.camera_yaw += delta.x * 0.1
            self.camera_pitch += delta.y * 0.1

            # Clamp pitch to avoid flipping
            self.camera_pitch = max(-89, min(89, self.camera_pitch))

    def wheelEvent(self, event):
        # Zoom in/out
        delta = event.angleDelta().y() / 120
        self.camera_pos.z -= delta * 0.5
        self.camera_pos.z = max(1, self.camera_pos.z)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Soft-Body Physics")
        self.setGeometry(100, 100, 800, 600)

        # Create OpenGL widget
        self.gl_widget = GLWidget(self)
        self.setCentralWidget(self.gl_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())