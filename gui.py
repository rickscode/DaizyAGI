import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtGui import QFont,QPixmap
from PyQt5.QtCore import Qt
import main
from dotenv import load_dotenv
load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daizy AGI")
        self.setFixedSize(700, 500)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # creating label
        self.title_label = QLabel("Daizy", self.central_widget)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 20))
        self.title_label = QLabel(self)
         
        # loading image
        self.pixmap = QPixmap('logodaizyagi.png')
 
        # adding image to label
        self.title_label.setPixmap(self.pixmap)
        self.title_label.resize(self.pixmap.width(),
                          self.pixmap.height())

        self.input_label = QLabel("Enter An Objective:", self.central_widget)
        self.input_label.setFont(QFont("Arial", 14))

        self.input_text = QLineEdit(self.central_widget)
        self.input_text.setFont(QFont("Arial", 14))

        self.submit_button = QPushButton("Please Begin Task", self.central_widget)
        self.submit_button.setFont(QFont("Arial", 14))
        self.submit_button.clicked.connect(self.submit_task)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.input_label)
        self.layout.addWidget(self.input_text)
        self.layout.addWidget(self.submit_button)

    def submit_task(self):
        # Load environment variables from .env file
        load_dotenv()
        # Get input text from user
        input_text = self.input_text.text()

        # Pass input text to OpenAI model for processing and generate response
        response_text = main.generate_response(input_text)
        action = (response_text)

        if action["type"] == "search":
            # Perform Google search and get results
            search_results = main.google_search(action["query"])
            output_text = f"Search results:\n{search_results}"
        elif action["type"] == "write_file":
            # Write content to the specified file
            with open(action["file_name"], "w") as file:
                file.write(action["content"])
            output_text = f"Content has been written to {action['file_name']}"
        elif action["type"] == "text":
            output_text = action["content"]
        else:
            output_text = "Unknown action"

        # Show output to user and ask for permission to continue
        msg_box = QMessageBox()
        msg_box.setText(output_text)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        user_response = msg_box.exec_()
        user_approves = user_response == QMessageBox.Yes

        # If user approves, perform action and save input/output to database
        if user_approves:
            main.insert_interaction(input_text, action)

if __name__ == "__main__":
    print("Starting GUI")  # Add this line
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
