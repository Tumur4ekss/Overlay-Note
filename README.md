[Read in English](README.md) | [Читать на русском](README.ru.md)
# Overlay Note

**Overlay Note** is a compact and convenient Windows utility built with Python (Tkinter) that minimizes to the system tray, designed for quickly viewing clipboard content on top of all windows. 
The app automatically detects whether your clipboard contains text or an image and displays it in a floating window, while also providing a quick copy mode for notes.

---

## Key Features

* **Universal Overlay (`ALT+V`):**
  * If the clipboard contains an **image** (screenshot) — opens a compact floating window displaying the image on top of all windows.
  * If the clipboard contains **text** — opens a floating notepad with text editing and formatting support.
* **Quick Copy Mode (`ALT+B`):**
  * Opens a card with text from the clipboard. Clicking on the text instantly copies it back to the clipboard.
* **Text Drag-and-Drop:**
  * Ability to select and move text fragments using the mouse (holding LMB) inside the built-in notepad.
* **System Tray:**
  * Runs silently in the background and minimizes to the system tray.
* **Autosave & Localization:**
  * Support for **English** and **Russian** languages.
  * All settings (theme, language, hotkeys) are saved to `%APPDATA%\OverlayNote\config.json` and persist across restarts.



# Overlay Note

**Overlay Note** — это компактная и удобная утилита для Windows на Python (Tkinter),которая сворачивается в трей, предназначенная для быстрого просмотра содержимого буфера обмена поверх всех окон. 
Программа автоматически распознаёт, что находится в буфере — текст или изображение — и отображает его в плавающем окне, а также предоставляет режим быстрого копирования заметок.

---

## Основные возможности

* **Универсальный оверлей (`ALT+V`):**
  * Если в буфере обмена **картинка** (скриншот) — открывается компактное окно с изображением поверх всех окон.
  * Если в буфере **текст** — открывается плавающий блокнот с возможностью редактирования и форматирования.
* **Режим быстрого копирования (`ALT+B`):**
  * Открывает карточку с текстом из буфера. Клик по тексту мгновенно копирует его обратно в буфер обмена.
* **Перетаскивание текста (Drag-and-Drop):**
  * Возможность выделять и перемещать фрагменты текста мышью (удержанием ЛКМ) внутри встроенного блокнота.
* **Системный трей:**
  * Приложение работает в фоновом режиме, сворачивается в трей.
* **Автосохранение и Локализация:**
  * Поддержка **Английского** и **Русского** языков.
  * Все настройки (тема, язык, хоткеи) сохраняются в `%APPDATA%\OverlayNote\config.json` и не теряются при перезапуске.
