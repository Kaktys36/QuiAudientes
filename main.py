import sys
import whisper
import torch
import re
from pytube import YouTube
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTextEdit, QComboBox, QToolBar, QAction, QMessageBox, QProgressBar
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QFont
from PyQt5.QtCore import Qt

class AudioTranscriber(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = None
        self.transcribe_language = "ru"  # язык транскрибации по умолчанию
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 600, 600) #Рамка
        self.setWindowTitle('QuiAudientes_v.0.a(AudioTranscriber)') #Название приложения

        central_widget = QWidget()
        layout = QVBoxLayout() # Менеджер компановки

        # Текст для пользователя о вводе ссылки
        self.link_label = QLabel('Введите ссылку на видео YouTube:', self)
        self.link_label.setFont(QFont("Comic Sans MS", 18))
        self.link_label.setStyleSheet('color: Black;')
        layout.addWidget(self.link_label)
        
        # Редактор текста для ввода ссылки
        self.link_edit = QTextEdit(self)
        self.link_edit.setStyleSheet('font-size: 10pt;')
        self.link_edit.setMaximumHeight(70)
        layout.addWidget(self.link_edit)
        
        # Текст для пользователя о полученном тексте
        self.text_label = QLabel('Транскрибированный текст:', self)
        self.text_label.setFont(QFont("Comic Sans MS", 18))
        self.text_label.setStyleSheet('color: Black;')
        layout.addWidget(self.text_label)

        # Редактор текста для полученного текста
        self.text_edit = QTextEdit(self)
        self.text_edit.setStyleSheet('font-size: 14pt;')
        layout.addWidget(self.text_edit)
        
        # Текст о ходе выполнения программы
        self.progress_label = QLabel('Ход выполнения программы:')
        self.progress_label.setFont(QFont("Comic Sans MS", 18))
        layout.addWidget(self.progress_label)

        # В будущем обновляемый текстовый элемент для отображения процесса выполнения программы
        self.progress_info = QLabel('', self)
        self.progress_info.setFont(QFont("Comic Sans MS", 14))
        self.progress_info.setStyleSheet('color: Purple;')
        layout.addWidget(self.progress_info)

        # Кнопка для запуска транскрибации
        self.button_load = QPushButton('Транскрибировать', self)
        self.button_load.setFont(QFont("Comic Sans MS", 18))
        self.button_load.clicked.connect(self.download_and_transcribe_audio) # Подключение функции которая будет выполняться при нажатии на кнопку
        layout.addWidget(self.button_load)

        # Кнопка для сохранения полученного текста
        self.save_button = QPushButton('Выбрать место сохранения текстового файла', self)
        self.save_button.setFont(QFont("Comic Sans MS", 18))
        self.save_button.clicked.connect(self.save_text_file)
        layout.addWidget(self.save_button)
        
        # Код для организации расположения виджетов
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Фон
        pixmap = QPixmap('C:\\Users\\YourName\\Desktop\\background.jpg') # Путь к фону программы
        self.palette = QPalette()
        self.palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(self.palette)

        # Текст для пользователя о корпусе виспера
        self.size_label = QLabel('Модель транскибатора:')
        self.size_label.setFont(QFont("Comic Sans MS", 16))
        layout.addWidget(self.size_label)
        
        # Список для выбора корпуса
        self.size_combobox = QComboBox(self)
        self.size_combobox.setStyleSheet('font-size: 16pt;')
        self.size_combobox.addItem("tiny")
        self.size_combobox.addItem("base")
        self.size_combobox.addItem("small")
        self.size_combobox.addItem("medium")
        self.size_combobox.addItem("large")
        self.size_combobox.addItem("large-v2. Поддерживает перевод")
        self.size_combobox.addItem("large-v3. Поддерживает перевод")
        self.size_combobox.currentIndexChanged.connect(self.change_whisper_size)
        layout.addWidget(self.size_combobox)

        # Текст для пользователя о выборе языка
        self.language_label = QLabel('Выберите язык для транскрибации:', self)
        self.language_label.setFont(QFont("Comic Sans MS", 18))
        self.language_label.setStyleSheet('color: Black;')
        layout.addWidget(self.language_label)

        # Список для выбора языка
        self.language_combobox = QComboBox(self)
        self.language_combobox.setStyleSheet('font-size: 16pt;')
        self.language_combobox.addItem("Русский")
        self.language_combobox.addItem("Английский")
        self.language_combobox.addItem("Французский")
        self.language_combobox.addItem("Испанский")
        self.language_combobox.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.language_combobox)

        # Панель инструментов
        toolbar = self.addToolBar('ToolBar')

        # Действие для открытия информации о программе
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about_dialog) # Привязывается функция с информацией. Далее тоже самое для других элементов
        toolbar.addAction(about_action)
        manual_action = QAction('Инструкция по использованию', self)
        manual_action.triggered.connect(self.show_manual_dialog)
        toolbar.addAction(manual_action)
        support_action = QAction('Поддержать разработчика', self)
        support_action.triggered.connect(self.show_support_dialog)
        toolbar.addAction(support_action)

    # Функция для смены языка транскрибации
    def change_language(self, index):
        languages = ["ru", "en", "fr", "es"]
        language = languages[index]
        self.update_progress_info(f"Выбран язык для транскрибации: {language}.") # Обновление о ходе выполнения программы
        self.transcribe_language = language
    
    # О программме
    def show_about_dialog(self):
        about_text = '''
QuiAudientes_v.0.a. Название происходит от английского "слушатель".
Программа предназначена для транскрибации аудио с видео YouTube. 

Логика работы программы примерно следущая: 
    1. Пользователь указывает размер whisper. Whisper-модель машинного обучения от Google, предназначенная для получения текстовой информации из аудиопотока.
    2. Пользователь указывает ссылку на видео в ютуб.
    3. Программа скачивает аудиопоток с этого видео.
    4. Данные передаются в whisper.
    5. Транскрибированный текст передаётся в специальное поле для того, чтобы его можно было просмотреть пользователю.
    6. При необходимости пользователь может сохранить тект в файл-блокнот.

Страница разработчика на github: 
\thttps://github.com/Kaktys36 
Telegram: 
\t@KiloLex
                      '''
        QMessageBox.about(self, "О программе", about_text) # Окно оповещения, будет вызываться при нажатии на кнопку

    # Инструкция по использованию
    def show_manual_dialog(self):
        manual_text = '''
    1. Выберите размер whisper с помощью которого будет происходить транскрибация. Чем он больше, тем качество полученного текста выше будет выше. При этом время, необходимое для транскрибации также увеличится. Учитывайте, что при выборе модели, если ранее Вы её не использовали-придётся ждать её загрузки.
    2. Вставьте ссылку на нужное видео в соответсвующее поле.
    3. Нажмите кнопку "Транскрибировать" и дождитесь выполнения программы.
    4. При необходимости можно сохранить полученный текст в формате файла-блокнота, нажав на соответсвующую кнопку.
                      '''
        QMessageBox.about(self, "Инструкция по использованию", manual_text)

    # Поддержать разработчика
    def show_support_dialog(self):
        support_text = '''
Поддержать разработчика можно с помощью пожертвования или с помощью предложений по улучшению. Контакты указаны в разделе "О программе".
Номер карты (Сбер, СБП): 
\t2202201869695284
                        '''
        QMessageBox.about(self, "Поддержать разработчика", support_text)

    # Функция для изменения корпуса виспера
    def change_whisper_size(self, index):
        sizes = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        size = sizes[index]
        self.model = self.get_model(size)
        self.update_progress_info(f"Размер Whisper изменен на {size}.")

    # Получение модели
    def get_model(self, size):
        if self.model:
            del self.model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = whisper.load_model(size).to(device)
        return model

    # Функция обновления информации о ходе программы
    def update_progress_info(self, message):
        self.progress_info.setText(message)

    # Функция для скачивания аудиопотока с видео ютуб
    def download_audio_from_link(self, link):
        self.update_progress_info("Загрузка аудио с YouTube...")
        try:
            video = YouTube(link)
        except:
            self.update_progress_info("Ошибка при загрузке видео. Пожалуйста, убедитесь в корректности ссылки.")
            return None, None

        streams = video.streams.filter(only_audio=True).order_by("abr").desc()

        if streams:
            highest_quality_audio = streams[0]
            clean_title = re.sub(r'[\\/*?:"<>|]', "_", video.title) # Убирает символы из названия видео, которые могут вызвать ошибку
            file_path = f"{clean_title}.mp3"
            highest_quality_audio.download(filename=file_path)

            with open(file_path, "rb") as file:
                audio_content = file.read()

            self.update_progress_info("Аудио максимального качества успешно загружено!")
            return audio_content, file_path
        else:
            self.update_progress_info("Аудио не найдено для данного видео.")
            return None, None

    # Функция непосредственно транскрибации
    def audio_to_text(self, audio_content):
        result = self.model.transcribe(audio_content, language=self.transcribe_language, fp16=True, verbose=True)
        text = result['text']
        self.update_progress_info("Транскрибация закончена.")
        return text
    
    # Функция, которая объединяет функцию скачивания аудио и транскрибацию
    def download_and_transcribe_audio(self):
        link = self.link_edit.toPlainText()
        audio_content, file_path = self.download_audio_from_link(link)

        if audio_content and file_path:
            self.update_progress_info("Транскрибация в процессе...")
            QApplication.processEvents()

            text = self.audio_to_text(file_path)
            self.text_edit.setPlainText(text)
        else:
            self.text_edit.setPlainText('Ошибка при загрузке аудио с YouTube')

    # Функция для сохранения файлов
    def save_text_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, 'Сохранить файл', '', 'Text files (*.txt)')
        if file_path:
            with open(file_path, 'wb') as file:
                file.write(self.text_edit.toPlainText().encode('utf-8'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioTranscriber()
    window.show()
    sys.exit(app.exec_())