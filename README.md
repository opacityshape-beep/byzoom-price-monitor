# 💪 BYZOOM FITNESS 每日巡價監控工具

每天早上 9:00 自動巡邏各電商平台，發現破價立刻寄 Email 通知你！

---

## 📦 監控平台

- momo 購物網
- PChome 24h
- Yahoo 購物中心
- 蝦皮購物
- 酷澎 Coupang

---

## 🚀 設定步驟（照順序做，大約 15 分鐘）

### Step 1：建立 GitHub 帳號

1. 前往 https://github.com 註冊免費帳號
2. 完成 Email 驗證

---

### Step 2：建立這個程式的 Repository

1. 登入 GitHub 後，點右上角 **+** → **New repository**
2. Repository name 填：`byzoom-price-monitor`
3. 選 **Private**（私人，別人看不到）
4. 點 **Create repository**

---

### Step 3：上傳程式碼

把整個資料夾的檔案上傳到你的 Repository：

**方法 A（最簡單）：直接在網頁上傳**

1. 進入你的 Repository 頁面
2. 點 **uploading an existing file**
3. 把以下兩個資料夾整個拖進去：
   - `src/` 資料夾（含 `monitor.py`）
   - `.github/` 資料夾（含 `workflows/price_monitor.yml`）
4. 點 **Commit changes**

---

### Step 4：設定 Gmail 應用程式密碼

> Gmail 不能直接用帳號密碼寄信，要申請「應用程式密碼」

1. 前往 https://myaccount.google.com/security
2. 確認已開啟**兩步驟驗證**
3. 搜尋「應用程式密碼」
4. 選擇「郵件」→「Windows 電腦」→ 產生
5. 記下那 16 碼密碼（只顯示一次！）

---

### Step 5：在 GitHub 設定 Secrets（存放帳密）

1. 進入你的 Repository → **Settings** → **Secrets and variables** → **Actions**
2. 點 **New repository secret**，新增以下 3 個：

| Secret 名稱 | 填入內容 |
|------------|---------|
| `GMAIL_USER` | 你的 Gmail 地址（例：abc@gmail.com）|
| `GMAIL_PASSWORD` | Step 4 取得的 16 碼應用程式密碼 |
| `NOTIFY_EMAIL` | 你要收通知的 Email |

---

### Step 6：測試執行

1. 進入 Repository → **Actions** 頁籤
2. 點左側 **BYZOOM 每日巡價監控**
3. 點右上 **Run workflow** → **Run workflow**
4. 等約 5~10 分鐘，看看有沒有收到 Email ✉️

---

## ⏰ 執行時間

每天早上 **09:00（台灣時間）** 自動執行。

也可以到 Actions 頁面手動點 **Run workflow** 隨時執行。

---

## 📧 Email 通知說明

| 狀況 | Email 主旨 |
|------|-----------|
| 發現破價 | 🚨【BYZOOM破價警報】發現 N 筆破價！|
| 一切正常 | ✅【BYZOOM巡價報告】今日正常 |

---

## ❓ 常見問題

**Q：沒收到 Email 怎麼辦？**
先查 Actions 頁面有沒有錯誤訊息（紅色 ✗）→ 點進去看 log。

**Q：可以增加監控平台嗎？**
可以！在 `src/monitor.py` 裡新增搜尋函數，再加到 `find_price_violations` 裡的 searcher 清單。

**Q：可以改執行時間嗎？**
修改 `.github/workflows/price_monitor.yml` 裡的 `cron` 設定。
例如改成早上 8:00：`0 0 * * *`

---

## 📁 檔案結構

```
byzoom-price-monitor/
├── src/
│   └── monitor.py          # 主程式
├── .github/
│   └── workflows/
│       └── price_monitor.yml  # 自動排程設定
└── README.md               # 這份說明文件
```
