.class public final Lcom/ifengyu/intercom/LocalFirmware;
.super Ljava/lang/Object;
.source "LocalFirmware.java"


# Mi-Walkie-Talkie-Plus: the official firmware-update server is offline, so the
# "Firmware Update" button's online version check never answers and the update
# screen (where Darkhorse's local-file flashing lives) never opens. When the
# Mi-walkie-talkie.firmware folder exists and a radio is connected, open the
# update screen directly with a placeholder update description instead.


# direct methods
.method private constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

# Returns true if the update screen was opened, false to fall back to the
# original (online) behaviour.
.method public static startSealUpdate(Landroid/app/Activity;)Z
    .locals 4

    new-instance v0, Ljava/io/File;

    invoke-static {}, Landroid/os/Environment;->getExternalStorageDirectory()Ljava/io/File;

    move-result-object v1

    const-string v2, "Mi-walkie-talkie.firmware"

    invoke-direct {v0, v1, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/io/File;->isDirectory()Z

    move-result v0

    if-nez v0, :cond_folder

    const/4 v0, 0x0

    return v0

    :cond_folder
    invoke-static {}, Lcom/ifengyu/intercom/node/j;->b()Lcom/ifengyu/intercom/node/j;

    move-result-object v0

    invoke-virtual {v0}, Lcom/ifengyu/intercom/node/j;->a()Z

    move-result v0

    if-nez v0, :cond_connected

    const/4 v0, 0x0

    return v0

    :cond_connected
    new-instance v0, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;

    invoke-direct {v0}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;-><init>()V

    const-string v1, "1"

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setVersionCode(Ljava/lang/String;)V

    const-string v1, "local"

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setVersionName(Ljava/lang/String;)V

    const-string v1, ""

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setSource(Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setMD5(Ljava/lang/String;)V

    const-string v1, "Firmware from the Mi-walkie-talkie.firmware folder"

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setInfo(Ljava/lang/String;)V

    const-string v1, "en"

    invoke-virtual {v0, v1}, Lcom/ifengyu/intercom/bean/McuUpdateInfoModel;->setLang(Ljava/lang/String;)V

    new-instance v1, Landroid/content/Intent;

    const-class v2, Lcom/ifengyu/intercom/ui/activity/SealSharkMcuUpdateActivity;

    invoke-direct {v1, p0, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v2, "mcu_update_device_type"

    const-string v3, "seal"

    invoke-virtual {v1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v2, "mcu_have_update"

    const/4 v3, 0x1

    invoke-virtual {v1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Z)Landroid/content/Intent;

    const-string v2, "mcu_update_info"

    invoke-virtual {v1, v2, v0}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Parcelable;)Landroid/content/Intent;

    const-string v2, "mcu_update_action_from_setting"

    invoke-virtual {v1, v2}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    invoke-virtual {p0, v1}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V

    const/4 v0, 0x1

    return v0
.end method
