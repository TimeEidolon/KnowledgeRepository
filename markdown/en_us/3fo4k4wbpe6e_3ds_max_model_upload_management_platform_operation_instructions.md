Coohom supports uploading 3ds Max models. This article will explain in detail how to use the 3ds Max model upload management platform to facilitate you to upload models more smoothly.

For Users
=========

**All users**, the function is gradually being opened.

Download and Installation
=========================

**1. Download**

① Enter theworkspace, select **Models** , and find **Model Management Platform**.

![](https://qhstaticssl.kujiale.com/image/png/1778222825023/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

② Move the mouse over the icon and click **Plugin Download** to download the .exe file.

![](https://qhstaticssl.kujiale.com/image/png/1778222944553/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

**2. Installation**

Click the .exe file to install it, select the language you want to install, and the plugin will be installed in 3ds Max.

* **Supported versions: 3ds Max 2021 and 3ds Max 2023**

![](https://qhstaticssl.kujiale.com/image/png/1747279556486/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

![](https://qhstaticssl.kujiale.com/yuntai/image/jpeg/1747279600440/A0774C34F1E9184C768D5F5C9C280E17.png)

Plugin Usage
============

**1. Plugin Features**

① After successful installation, open **3ds Max** , and you'll see a new menu item: **CooVerse (K)** in the top menu bar.

![](https://qhstaticssl.kujiale.com/image/png/1747277685902/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

② Click **CooVerse (K)** to open the plugin window, which includes three main sections:

* **User Account**
* **Project**
* **Model**

![](https://qhstaticssl.kujiale.com/yuntai/image/jpeg/1747279880634/6CC3AA71E1541E7D1C36EF830ACC2A3A.png)

**2.** **Upload Models**

**① Log in (Required)**

Click **Log in**, enter your Coohom account credentials in the pop-up window, then click the refresh button to complete the login process.

![](https://qhstaticssl.kujiale.com/image/png/1747279997838/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

**② Create Project (Required)**

Click **Create** to make a new project folder. Uploaded models will be stored in the corresponding project folder.

![](https://qhstaticssl.kujiale.com/yuntai/image/jpeg/1747275523297/E35B15ADF44B665E560766E13CBD60E3.png)

**③ Upload Model**

Open a local .max file on your computer. Click **Upload Model**. Once the cloud processing reaches 100%, the upload is successful.

![](https://qhstaticssl.kujiale.com/image/png/1747281457893/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

**④ Add to Library**

After the transfer is complete, open **Models** and click**Model Management Platform** , select the model, and click **Archive**.

![](https://qhstaticssl.kujiale.com/image/png/1778223019229/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

![](https://qhstaticssl.kujiale.com/image/png/1778223231743/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

**⑤ Finalize Upload**

After adding to the library, select the **model category** and **location**, then complete the model upload.

![](https://qhstaticssl.kujiale.com/image/png/1778223448945/A8CEBABD0663ECBAEEE7516DF7A7D2B5.png)

Notes and Requirements
======================

1. 3ds Max must be installed locally before using the plugin. Currently, only **3ds Max 2021** and **2023** are supported.

2. Currently, **only V-Ray for 3ds Max** is supported. Please set the render engine to V-Ray before uploading.

3. It is recommended to use **V-Ray 4** for optimal results. **V-Ray 5 and above** may result in rendering inconsistencies.

4. This feature is **only available to selected users**.

Troubleshooting: Plugin Not Responding After Installation
=========================================================

If the **CooVerse plugin does not respond** **when clicked after installation**, it may be caused by one of the following issues. Try the corresponding solutions below:

|                 **Possible Causes**                 |                                                                                                                                                    **Solution**                                                                                                                                                     |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Plugin files are corrupted.                         | 1. Download the required **Python folder** and extract it ---[\[Click to Download\]](https://user-platform-oss.kujiale.com/upms/direct/63f9d2eadd6896b1-1740621401692-1.zip?kjl_source=hc) 2. Replace the original python folder in your 3ds Max installation directory with the extracted one. 3. Restart 3ds Max. |
| Missing required dependencies.                      | Make sure you have installed the **latest version of the Visual C++ Redistributable** --- [\[Click to Download\]](https://user-platform-oss.kujiale.com/upms/direct/6168acb493447cdb-1741921563578-1.exe?kjl_source=hc)                                                                                             |
| Plugin is not compatible with your 3ds Max version. | Try using the **3ds Max 2023 base version**, which is more compatible with the plugin.                                                                                                                                                                                                                              |
