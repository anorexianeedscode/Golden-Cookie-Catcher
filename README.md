# Golden Cookie Catcher

Авто-ловля золотых печенек в Cookie Clicker. Шаблон вшит в сборку — пользователь ничего не настраивает.

## Сборка

1. `pip install -r requirements.txt`
2. Иконку положи в `assets/icon_src.png`
3. `build.bat` → `dist\GoldenCookieCatcher.exe`
4. `iscc installer.iss` → инсталлятор

## Отладка

В `build.spec` поставь `console=True`, чтобы видеть трейсбеки.

## Настройки

`settings.json` рядом с exe, при отсутствии прав — в `%APPDATA%\GoldenCookieCatcher`.