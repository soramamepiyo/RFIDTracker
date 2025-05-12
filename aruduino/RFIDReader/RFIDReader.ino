#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN 9      // RC522 RST
#define SS_PIN 8      // RC522 SDA/SS

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  while (!Serial); // for Leonardo/Micro
  SPI.begin();
  mfrc522.PCD_Init();
  delay(4);
  Serial.println("RC522 Reader Ready");
}

void loop() {
  // RFIDタグの検出待ち
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  // UIDの出力
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10)
      Serial.print("0");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.println();

  // 読み取り後のクールタイム
  delay(1000);
}
