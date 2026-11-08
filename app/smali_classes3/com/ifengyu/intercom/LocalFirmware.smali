.class public final Lcom/ifengyu/intercom/LocalFirmware;
.super Ljava/lang/Object;
.source "LocalFirmware.java"


# Mi-Walkie-Talkie-Plus: the official firmware-update server is offline, so the
# "Firmware Update" button's online version check never answers and the update
# screen (where Darkhorse's local-file flashing lives) never opens. When the
# Mi-walkie-talkie.firmware folder holds a file for the connected radio's
# hardware revision, open the update screen directly with a placeholder update
# description instead.
#
# The update screen only flashes a local file if one matches
# "seal_*_hw<revision>.bin"; otherwise it would try to download using the
# placeholder (and crash), so the screen is opened only after the same check.


# direct methods
.method private constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

# Returns true if handled (update screen opened, permission requested, or an explanation shown),
# false to fall back to the original (online) behaviour.
.method public static startSealUpdate(Landroid/app/Activity;)Z
    .locals 8

    # Reading the firmware folder needs storage permission, which the app
    # otherwise only requests on unrelated screens. Ask for it here if missing.
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v2, 0x17

    if-lt v1, v2, :cond_perm_ok

    const-string v1, "android.permission.READ_EXTERNAL_STORAGE"

    invoke-virtual {p0, v1}, Landroid/app/Activity;->checkSelfPermission(Ljava/lang/String;)I

    move-result v2

    if-eqz v2, :cond_perm_ok

    const/4 v2, 0x2

    new-array v2, v2, [Ljava/lang/String;

    const/4 v3, 0x0

    aput-object v1, v2, v3

    const-string v1, "android.permission.WRITE_EXTERNAL_STORAGE"

    const/4 v3, 0x1

    aput-object v1, v2, v3

    const/16 v3, 0x15

    invoke-virtual {p0, v2, v3}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V

    const-string v1, "Allow storage access so the app can read the Mi-walkie-talkie.firmware folder, then press Firmware Update again."

    const/4 v2, 0x1

    invoke-static {v1, v2}, Lcom/ifengyu/intercom/i/c0;->a(Ljava/lang/CharSequence;Z)V

    const/4 v1, 0x1

    return v1

    :cond_perm_ok
    new-instance v0, Ljava/io/File;

    invoke-static {}, Landroid/os/Environment;->getExternalStorageDirectory()Ljava/io/File;

    move-result-object v1

    const-string v2, "Mi-walkie-talkie.firmware"

    invoke-direct {v0, v1, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/io/File;->isDirectory()Z

    move-result v1

    if-nez v1, :cond_folder

    const/4 v1, 0x0

    return v1

    :cond_folder
    invoke-static {}, Lcom/ifengyu/intercom/node/j;->b()Lcom/ifengyu/intercom/node/j;

    move-result-object v1

    invoke-virtual {v1}, Lcom/ifengyu/intercom/node/j;->a()Z

    move-result v1

    if-nez v1, :cond_connected

    const/4 v1, 0x0

    return v1

    :cond_connected
    # v3 = hardware revision reported by the radio, v4 = "_hw<rev>.bin"
    invoke-static {}, Lcom/ifengyu/intercom/i/d0;->C()I

    move-result v3

    new-instance v4, Ljava/lang/StringBuilder;

    const-string v1, "_hw"

    invoke-direct {v4, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    const-string v1, ".bin"

    invoke-virtual {v4, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v0}, Ljava/io/File;->list()[Ljava/lang/String;

    move-result-object v5

    if-eqz v5, :cond_nofile

    array-length v6, v5

    const/4 v2, 0x0

    :goto_loop
    if-ge v2, v6, :cond_nofile

    aget-object v7, v5, v2

    invoke-virtual {v7}, Ljava/lang/String;->toLowerCase()Ljava/lang/String;

    move-result-object v7

    const-string v1, "seal_"

    invoke-virtual {v7, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :cond_next

    invoke-virtual {v7, v4}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v1

    if-nez v1, :cond_found

    :cond_next
    add-int/lit8 v2, v2, 0x1

    goto :goto_loop

    :cond_nofile
    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "No firmware file for this radio in Mi-walkie-talkie.firmware. Expected a name like seal_..."

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v2, " (radio reports hardware revision "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    const-string v2, ")."

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const/4 v2, 0x1

    invoke-static {v1, v2}, Lcom/ifengyu/intercom/i/c0;->a(Ljava/lang/CharSequence;Z)V

    const/4 v1, 0x1

    return v1

    :cond_found
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
