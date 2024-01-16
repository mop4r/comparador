import sys
import pyodbc
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox,
    QDialog, QProgressBar, QLabel, QTextBrowser, QMessageBox, QInputDialog, QRadioButton, QHBoxLayout, QDesktopWidget, QCheckBox, QScrollArea, QGridLayout
)
from PyQt5.QtCore import QThread, pyqtSignal


class ColumnSelectionWindow(QDialog):
    columns_selected = pyqtSignal(list)

    def __init__(self, table_name, columns):
        super().__init__()
        self.setWindowTitle("Column Selection")
        self.setGeometry(200, 200, 600, 400)  # Tamanho ajustado

        self.table_name = table_name
        self.columns = columns

        # Crie um QScrollArea para permitir rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Define o widget rolável
        self.setFixedSize(600, 400)  # Define o tamanho da janela
        layout = QVBoxLayout(self)  # Usando um layout vertical na janela principal
        layout.addWidget(scroll_area)  # Adiciona o QScrollArea ao layout da janela principal

        # Crie um QWidget dentro do QScrollArea
        container = QWidget(scroll_area)
        scroll_area.setWidget(container)

        container_layout = QVBoxLayout()  # Usando um layout vertical para o container

        self.checkbox_list = []

        # Organize as colunas em uma grade
        num_columns = len(self.columns)
        num_columns_per_row = 5  # Defina o número de colunas por linha
        row = 0
        col = 0

        for column in self.columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            container_layout.addWidget(checkbox)  # Adiciona checkboxes ao layout do container
            self.checkbox_list.append(checkbox)

            col += 1
            if col >= num_columns_per_row:
                col = 0
                row += 1

        select_all_button = QPushButton("Select All")
        deselect_all_button = QPushButton("Deselect All")
        apply_button = QPushButton("Apply")

        select_all_button.clicked.connect(self.select_all_columns)
        deselect_all_button.clicked.connect(self.deselect_all_columns)
        apply_button.clicked.connect(self.apply_column_selection)

        container_layout.addWidget(select_all_button)
        container_layout.addWidget(deselect_all_button)
        container_layout.addWidget(apply_button)

        container.setLayout(container_layout)

    def select_all_columns(self):
        for checkbox in self.checkbox_list:
            checkbox.setChecked(True)

    def deselect_all_columns(self):
        for checkbox in self.checkbox_list:
            checkbox.setChecked(False)

    def apply_column_selection(self):
        selected_columns = [checkbox.text() for checkbox in self.checkbox_list if checkbox.isChecked()]
        if not selected_columns:
            QMessageBox.warning(self, "Warning", "Please select at least one column.")
        else:
            self.columns_selected.emit(selected_columns)
            self.accept()

class ComparisonThread(QThread):
    update_progress = pyqtSignal(int)
    comparison_done = pyqtSignal(list, list)

    def __init__(self, db1, db2, table_name, sql_condition, selected_columns):
        super().__init__()
        self.db1 = db1
        self.db2 = db2
        self.table_name = table_name
        self.sql_condition = sql_condition
        self.selected_columns = selected_columns

    def run(self):
        try:
            conn1 = pyodbc.connect(f"DSN={self.db1}")
            conn2 = pyodbc.connect(f"DSN={self.db2}")

            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()

            total_rows_db1 = 0
            total_rows_db2 = 0

            try:
                # Verifica se há uma condição SQL para incluir na consulta de contagem
                if self.sql_condition:
                    cursor1.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE {self.sql_condition}")
                    total_rows_db1 = cursor1.fetchone()[0]

                    cursor2.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE {self.sql_condition}")
                    total_rows_db2 = cursor2.fetchone()[0]
                else:
                    cursor1.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                    total_rows_db1 = cursor1.fetchone()[0]

                    cursor2.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                    total_rows_db2 = cursor2.fetchone()[0]
            except pyodbc.Error as e:
                # Trate a exceção de erro do banco de dados aqui
                error_message = f"Erro de consulta SQL: {str(e)}"
                self.error_occurred.emit(error_message)

            total_rows = max(total_rows_db1, total_rows_db2)
            selected_columns_str = ", ".join(self.selected_columns)

            if self.sql_condition:
                if self.selected_columns:
                    cursor1.execute(
                        f"SELECT {', '.join(self.selected_columns)} FROM {self.table_name} WHERE {self.sql_condition}")
                    cursor2.execute(
                        f"SELECT {', '.join(self.selected_columns)} FROM {self.table_name} WHERE {self.sql_condition}")
                else:
                    cursor1.execute(f"SELECT * FROM {self.table_name} WHERE {self.sql_condition}")
                    cursor2.execute(f"SELECT * FROM {self.table_name} WHERE {self.sql_condition}")
            else:
                if self.selected_columns:
                    cursor1.execute(f"SELECT {', '.join(self.selected_columns)} FROM {self.table_name}")
                    cursor2.execute(f"SELECT {', '.join(self.selected_columns)} FROM {self.table_name}")
                else:
                    cursor1.execute(f"SELECT * FROM {self.table_name}")
                    cursor2.execute(f"SELECT * FROM {self.table_name}")

            result_db1 = []
            result_db2 = []

            processed_rows = 0  # Inicializa o número de linhas processadas

            while True:
                row1 = cursor1.fetchone()
                row2 = cursor2.fetchone()

                if not row1 and not row2:
                    break

                processed_rows += 1  # Atualiza o número de linhas processadas
                progress = int(processed_rows / total_rows * 100)
                self.update_progress.emit(progress)  # Emitir progresso em tempo real
                """
                if row1 != row2:
                    if row1:
                        result_db1.append(row1)
                    if row2:
                        result_db2.append(row2)

                """
                if row1 != row2:
                    if row1:
                        columns = [column[0] for column in cursor1.description]
                        values = []
                        for val in row1:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                # Duplica as aspas simples e as barras invertidas
                                val = val.replace("\\", "\\\\").replace("'", "''")
                                values.append(f"'{val}'")
                            else:
                                values.append(str(val))
                        row1_str = ', '.join(values)
                        result_db1.append(f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({row1_str})")
                    if row2:
                        columns = [column[0] for column in cursor2.description]
                        values = []
                        for val in row2:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                # Duplica as aspas simples e as barras invertidas
                                val = val.replace("\\", "\\\\").replace("'", "''")
                                values.append(f"'{val}'")
                            else:
                                values.append(str(val))
                        row2_str = ', '.join(values)
                        result_db2.append(f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({row2_str})")


            self.comparison_done.emit(result_db1, result_db2)  # Emitir o sinal após o término da comparação

        except pyodbc.Error as e:
            error_message = f"Erro de conexão: {str(e)}"
            self.error_occurred.emit(error_message)  # Emitir mensagem de erro
        except Exception as e:
            error_message = f"Erro: {str(e)}"
            self.error_occurred.emit(error_message)  # Emitir mensagem de erro
        finally:
            conn1.close()
            conn2.close()


class ResultDialog(QDialog):
    def __init__(self, db1, db2, table_name, result_db1, result_db2):
        super().__init__()
        self.setWindowTitle("Resultado da Comparação")
        self.setGeometry(200, 200, 800, 400)

        # Guarde o nome da tabela como um atributo da instância
        self.table_name = table_name

        layout = QVBoxLayout()

        # Adicione os botões "Insert" e "Valores" em um QHBoxLayout
        button_layout = QHBoxLayout()
        self.insert_button = QRadioButton("Insert")
        self.values_button = QRadioButton("Valores")
        button_layout.addWidget(self.insert_button)
        button_layout.addWidget(self.values_button)

        self.label_db1 = QLabel(f"{len(result_db1)} Registros presentes somente no banco {db1} na tabela {table_name}:")

        self.text_browser_db1 = QTextBrowser()
        self.text_browser_db1.setLineWrapMode(QTextBrowser.NoWrap)
        self.text_browser_db1.setOpenExternalLinks(True)
        self.text_browser_db1.setReadOnly(True)

        copy_button_db1 = QPushButton("Copiar do Banco 1")

        # Use uma função lambda para passar o nome da tabela ao método copy_result
        copy_button_db1.clicked.connect(lambda: self.copy_result(result_db1, self.table_name))

        self.label_db2 = QLabel(f"{len(result_db2)} Registros presentes somente no banco {db2} na tabela {table_name}:")
        self.text_browser_db2 = QTextBrowser()
        self.text_browser_db2.setLineWrapMode(QTextBrowser.NoWrap)
        self.text_browser_db2.setOpenExternalLinks(True)
        self.text_browser_db2.setReadOnly(True)

        layout.addLayout(button_layout)  # Adicione o layout dos botões
        layout.addWidget(self.label_db1)
        layout.addWidget(self.text_browser_db1)
        layout.addWidget(copy_button_db1)
        layout.addWidget(self.label_db2)
        layout.addWidget(self.text_browser_db2)

        copy_button_db2 = QPushButton("Copiar do Banco 2")

        # Use uma função lambda para passar o nome da tabela ao método copy_result
        copy_button_db2.clicked.connect(lambda: self.copy_result(result_db2, self.table_name))

        layout.addWidget(copy_button_db2)

        self.setLayout(layout)

        # Conecte os sinais dos botões às funções de atualização do texto do QTextBrowser
        self.insert_button.toggled.connect(self.update_text_browser)
        self.values_button.toggled.connect(self.update_text_browser)

        # Armazene os resultados para uso posterior
        self.result_db1 = result_db1
        self.result_db2 = result_db2

        # Inicialmente, exiba os resultados como "Insert"
        self.insert_button.setChecked(True)
        self.update_text_browser()

    def copy_result(self, data, table_name):
        # Implemente a ação de copiar os registros, por exemplo, copiando-os para a área de transferência
        clipboard = QApplication.clipboard()

        if self.values_button.isChecked():
            # Se "Valores" está selecionado, copie os valores com parênteses de abertura e fechamento
            clipboard.setText("\n".join([f"({row.split('VALUES ')[1][1:-2]});" for row in data]))
        else:
            # Caso contrário, copie os dados como "Insert"
            clipboard.setText("\n".join([f"{str(row)};" for row in data]))

    def update_text_browser(self):
        # Atualize o conteúdo do QTextBrowser com base na seleção dos botões "Insert" ou "Valores"
        if self.insert_button.isChecked():
            self.text_browser_db1.setPlainText("\n".join([f"{str(row)};" for row in self.result_db1]))
            self.text_browser_db2.setPlainText("\n".join([f"{str(row)};" for row in self.result_db2]))
        elif self.values_button.isChecked():
            self.text_browser_db1.setPlainText(
                "\n".join([f"({row.split('VALUES ')[1][1:-2]});" for row in self.result_db1]))
            self.text_browser_db2.setPlainText(
                "\n".join([f"({row.split('VALUES ')[1][1:-2]});" for row in self.result_db2]))

class DatabaseComparer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Comparer")
        self.setGeometry(100, 100, 300, 300)

        # Centraliza a janela na tela
        screen_geometry = QDesktopWidget().screenGeometry()
        x = (screen_geometry.width() - self.width()) / 2
        y = (screen_geometry.height() - self.height()) / 2
        self.move(int(x), int(y))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        # Rótulos para as descrições
        label_db1 = QLabel("Selecione o Banco de dados 1:")
        label_db2 = QLabel("Selecione o Banco de dados 2:")
        label_table = QLabel("Selecione a tabela a ser comparada:")

        # ComboBoxes
        self.db1_label = QComboBox()
        self.db2_label = QComboBox()
        self.table_label = QComboBox()

        self.list_tables_button = QPushButton("Listar Tabelas em Comum")
        self.compare_button = QPushButton("Comparar Tabela")
        self.compare_button.setEnabled(False)  # Inicialmente, desabilite o botão

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.result_label = QLabel()
        self.layout.addWidget(self.result_label)

        # Adicione rótulos e ComboBoxes ao layout
        self.layout.addWidget(label_db1)
        self.layout.addWidget(self.db1_label)
        self.layout.addWidget(label_db2)
        self.layout.addWidget(self.db2_label)
        self.layout.addWidget(label_table)
        self.layout.addWidget(self.table_label)
        self.layout.addWidget(self.list_tables_button)
        self.layout.addWidget(self.compare_button)
        self.layout.addWidget(self.progress_bar)

        self.result_db1 = None
        self.result_db2 = None

        self.result_dialog = None

        self.column_selection_window = None
        self.selected_columns = []
        # Add a button for opening the column selection window
        self.column_selection_button = QPushButton("Select Columns")
        self.column_selection_button.setEnabled(False)
        self.layout.addWidget(self.column_selection_button)
        self.column_selection_button.clicked.connect(self.open_column_selection_window)

        # Botão para adicionar condição SQL
        self.add_sql_condition_button = QPushButton("Adicionar/Alterar Condição SQL (Sem o WHERE)")
        self.add_sql_condition_button.setEnabled(False)
        self.layout.addWidget(self.add_sql_condition_button)

        # Condição SQL inserida pelo usuário
        self.sql_condition = ""

        self.add_sql_condition_button.clicked.connect(self.add_or_edit_sql_condition)

        self.list_tables_button.clicked.connect(self.list_common_tables)
        self.compare_button.clicked.connect(self.compare_table)

        self.central_widget.setLayout(self.layout)

        self.populate_dsn_combobox(self.db1_label)
        self.populate_dsn_combobox(self.db2_label)

    def add_or_edit_sql_condition(self):
        text, ok = QInputDialog.getText(self, "Adicionar/Alterar Condição SQL", "Digite a condição SQL:", text=self.sql_condition)
        if ok:
            self.sql_condition = text

    def populate_dsn_combobox(self, combobox):
        try:
            dsn_list = pyodbc.dataSources()
            combobox.addItems(sorted(dsn_list.keys()))

        except Exception as e:
            print(f"Erro ao listar DSNs: {str(e)}")

    def list_common_tables(self):
        db1 = self.db1_label.currentText()
        db2 = self.db2_label.currentText()

        try:
            conn1 = pyodbc.connect(f"DSN={db1}")
            conn2 = pyodbc.connect(f"DSN={db2}")

            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()

            tables1 = sorted([row.table_name for row in cursor1.tables(tableType='TABLE')])
            tables2 = sorted([row.table_name for row in cursor2.tables(tableType='TABLE')])

            common_tables = sorted(list(set(tables1) & set(tables2)))

            self.table_label.clear()
            self.table_label.addItems(common_tables)

            self.result_label.setText('Tabelas comuns listadas com sucesso.')

        except pyodbc.Error as e:
            self.result_label.setText(f'Erro ao listar tabelas comuns: {str(e)}')
        finally:
            conn1.close()
            conn2.close()

        self.compare_button.setEnabled(True)
        self.add_sql_condition_button.setEnabled(True)
        self.column_selection_button.setEnabled(True)
    def block_ui(self):
        # Bloqueia todos os botões e ComboBoxes
        self.db1_label.setEnabled(False)
        self.db2_label.setEnabled(False)
        self.table_label.setEnabled(False)
        self.list_tables_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.add_sql_condition_button.setEnabled(False)
        self.column_selection_button.setEnabled(False)

    def unblock_ui(self):
        # Desbloqueia todos os botões e ComboBoxes
        self.db1_label.setEnabled(True)
        self.db2_label.setEnabled(True)
        self.table_label.setEnabled(True)
        self.list_tables_button.setEnabled(True)
        self.compare_button.setEnabled(True)
        self.add_sql_condition_button.setEnabled(True)
        self.column_selection_button.setEnabled(True)
    def compare_table(self):
        db1 = self.db1_label.currentText()
        db2 = self.db2_label.currentText()
        table_name = self.table_label.currentText()

        self.result_label.setText(f'Comparando tabela {table_name}...')

        # Bloqueia a interface do usuário durante a verificação
        self.block_ui()

        # Cria uma nova instância da classe ComparisonThread com a condição SQL
        self.comparison_thread = ComparisonThread(db1, db2, table_name, self.sql_condition, self.selected_columns)

        # Conecta os sinais e slots novamente
        self.comparison_thread.update_progress.connect(self.update_progress)
        self.comparison_thread.comparison_done.connect(self.show_comparison_result)
        self.comparison_thread.finished.connect(self.unblock_ui)  # Desbloqueia após a conclusão

        # Inicializa a barra de progresso com 0
        self.progress_bar.setValue(0)

        # Inicia a nova instância da thread
        self.comparison_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_comparison_result(self, result_db1, result_db2):
        self.result_db1 = result_db1
        self.result_db2 = result_db2

        db1 = self.db1_label.currentText()
        db2 = self.db2_label.currentText()
        table_name = self.table_label.currentText()

        if not result_db1 and not result_db2:
            # Caso ambos os resultados estejam vazios, exibe uma mensagem de igualdade em uma janela de aviso
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Resultado da Comparação")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(f'Todos os registros na tabela {table_name} dos bancos {db1} e {db2} são iguais.')
            msg_box.exec_()
        else:
            # Se houver registros diferentes, exibe a mensagem de comparação em uma janela de aviso
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Resultado da Comparação")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(f'Comparação concluída. Encontrados {len(result_db1)} registros diferentes em {db1} e {len(result_db2)} registros diferentes em {db2} na tabela {table_name}.')
            msg_box.setStandardButtons(QMessageBox.Ok)

            # Abre a janela de conteúdo dos registros somente após o usuário clicar em "OK"
            result = msg_box.exec_()

            if result == QMessageBox.Ok:
                if result_db1 or result_db2:
                    self.result_dialog = ResultDialog(db1, db2, table_name, result_db1, result_db2)
                    self.result_dialog.exec_()

    def open_column_selection_window(self):
        table_name = self.table_label.currentText()

        # Get the list of columns for the selected table
        db1 = self.db1_label.currentText()
        try:
            conn1 = pyodbc.connect(f"DSN={db1}")
            cursor1 = conn1.cursor()
            cursor1.execute(f"SELECT TOP 1 * FROM {table_name}")
            columns = [column[0] for column in cursor1.description]
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"Error retrieving columns: {str(e)}")
            return
        finally:
            conn1.close()

        self.column_selection_window = ColumnSelectionWindow(table_name, columns)

        # Connect the custom columns_selected signal to the handle_column_selection slot
        self.column_selection_window.columns_selected.connect(self.handle_column_selection)

        self.column_selection_window.exec_()

    def handle_column_selection(self, selected_columns):
        # Handle the selected columns
        self.selected_columns = selected_columns
        selected_columns_str = ", ".join(self.selected_columns)
        print("Selected columns:", self.selected_columns)
        print("Selected columns as a string:", selected_columns_str)

def main():
    app = QApplication(sys.argv)
    window = DatabaseComparer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()