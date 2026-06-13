# 🏥 Vet Anesthesia Records — เริ่มต้นใช้งาน

## วิธีเปิดโปรแกรม

### วิธีที่ 1: Double-click ไฟล์ shortcut (ง่ายที่สุด)

ไปที่โฟลเดอร์ `/Users/kriangkrai/claude/vet-anesthesia/`  
Double-click ไฟล์ชื่อ **`เปิดโปรแกรม.command`**

หรือใน **Desktop** มีไฟล์ **`เปิด Vet Anesthesia.command`**

---

### วิธีที่ 2: Terminal command

เปิด Terminal แล้วพิมพ์:
```bash
vet-anes
```

หรือพิมพ์เต็มรูปแบบ:
```bash
cd /Users/kriangkrai/claude/vet-anesthesia
bash start.sh
```

---

### วิธีที่ 3: cd เข้าโฟลเดอร์เอง

```bash
cd /Users/kriangkrai/claude/vet-anesthesia
bash start.sh
```

---

## หลังจากเปิดโปรแกรม

✅ รอให้ Terminal แสดง:
```
Uvicorn running on http://0.0.0.0:8100
```

✅ เปิด Browser แล้วไปที่: **http://localhost:8100**

✅ **Login:**
- Username: `admin`
- Password: `admin1234`

หรือ
- Username: `anesthesiologist`
- Password: `anes1234`

---

## ปิดโปรแกรม

กด `Ctrl+C` ใน Terminal

---

## ต้องการเปลี่ยน Port?

```bash
PORT=9000 bash start.sh
```

แล้วไปที่ `http://localhost:9000`
