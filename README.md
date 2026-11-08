## About
**Mi-Walkie-Talkie-Plus** is an improved version of original Xiaomi Mi Walkie-Talkie radios companion application for Android.  
**"Plus"** improvements are:
* **All the fancy Xiaomi frequency editing dialogs are replaced by simplified ones:**  
![alt text](http://cs5-3.4pda.to/14851033.jpg)  
These simplified dialogs allows to enter any frequency you want, in Megaherz, in 130 - 520 MHz range, with 1Hz precision (up to 6 fraction part digits). Original frequency dialogs are replaced both **for custom channels and repeaters for all supported walkie-talkie models.**  

* **Added the ability to install modified firmware.**  
Now you can use **Mi-Walkie-Talkie-Plus** app mod to flash custom firmware to all supported Xiaomi Mijia Walkie-Talkie radios. To do so, you should create the folder named "Mi-walkie-talkie.firmware" in your phone's internal memory, and put the correctly named firmware file(s) there. While such a folder exists, Mi-Walkie-Talkie-Plus believes that connected radio has firmware version "0.0.1", so the app will try to perform a firmware update. In case if there are any firmware files suitable for your radio model and revision in "Mi-walkie-talkie.firmware" folder, such a file will be flashed to the radio; otherwise, the latest official firmware version for your radio will be used (so you can revert to the official firmware by creating the empty "Mi-walkie-talkie.firmware" folder). <ins>Please, do not forget to remove or rename "Mi-walkie-talkie.firmware" folder upon the firmware update - otherwise, Mi-Walkie-Talkie-Plus continue to treat your radio firmware as version "0.0.1", and will not operate correctly.</ins>  

* **Language mapping rules are changed.**  
While original Mi Walkie-Talkie application has Chinese and English languages, it follows the rule: all non-English languages --> Chinese. It is not a problem if your phone's language is English or Chinese; but if your primary language is, for example, Spanish or Russian - Mi walkie-talkie application will use Chinese UI, and will update your walkie-talkie firmware to the Chinese version. **"Plus"** mod changes language mapping to the opposite: all non-Chinese phone languages --> English, so with Spanish primary language you will have English UI in application, and English walkie-talkie firmware updates.  

* **No account / login required (offline mode).**  
The ifengyu / Xiaomi account servers the original app signs into have been shut down, which made the login screen impossible to get past - and with it, channel programming. Everything the app does with the radio (scanning, connecting, activation, reading and writing channels, custom frequencies) happens locally over Bluetooth LE, so this build skips the login entirely: on first start it stores a local placeholder account and goes straight to connecting your radio. The forced "session expired" logout is removed as well. Online-only features (cloud channel configs, maps download, firmware download from the official server, feedback) still will not work, since those servers are gone.  

## Download
Downloads are available in project [Releases](https://github.com/Mi-Walkie-Talkie-by-Darkhorse/Mi-Walkie-Talkie-Plus/releases) section.

## Project structure
* **original-apk** - the original Mi-Walkie-Talkie Android application .apk is here.
* **original-java** - useful subset of the decompiled Java sources. It is not possible to build an application from theese sources - use it only as a human-readable reference.
* **app** - primary working folder to build **Mi-Walkie-Talkie-Plus** app mod.
    
## Building
Every push builds a signed APK with GitHub Actions (see `.github/workflows/build-apk.yml`); download it from the run's **Artifacts** section (`Mi-Walkie-Talkie-Plus-apk`). To keep the same signing key across builds (so new versions install as updates), add repository secrets `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD` and `KEY_ALIAS`; without them each build is signed with a throwaway key.  
Uninstall the original Mi Walkie-Talkie app (or any previous Plus build signed with a different key) before installing.

Use [Apktool](https://github.com/iBotPeaches/Apktool) v.2.4.0 or newer to build the **Mi-Walkie-Talkie-Plus** app mod.  
If you are interested in submitting a patch, feel free to send me a pull request here.
