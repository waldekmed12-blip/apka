[app]

title = Polski Asystent Predkosc
package.name = asystentpredkosci
package.domain = org.vadim

source.include_exts = py,png,jpg,kv,atlas
source.dir = .

version = 1.1

requirements = python3,kivy,requests,plyer,pyjnius

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1

fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WAKE_LOCK

android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
