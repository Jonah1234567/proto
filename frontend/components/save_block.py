from PyQt6.QtWidgets import QFileDialog, QPushButton

save_block_button = QPushButton("Save Block")
save_block_button.clicked.connect(self.save_current_block)

your_layout.addWidget(save_block_button)  # e.g., add to toolbar or a layout
