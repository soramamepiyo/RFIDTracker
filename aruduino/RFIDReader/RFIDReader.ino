#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN_1 7  // リーダー1のSDA（SS）ピン
#define SS_PIN_2 5   // リーダー2のSDA（SS）ピン
#define RST_PIN 9    // RSTは共通

MFRC522 rfid1(SS_PIN_1, RST_PIN);
MFRC522 rfid2(SS_PIN_2, RST_PIN);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid1.PCD_Init();
  rfid2.PCD_Init();
  Serial.println("Ready to read from 2 RC522 readers.");
}

void loop() {
  // リーダー1
  if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {
    Serial.print("1:");
    printUID(rfid1);
    rfid1.PICC_HaltA();
    rfid1.PCD_StopCrypto1();
    delay(1000);
  }

  // リーダー2
  if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {
    Serial.print("2:");
    printUID(rfid2);
    rfid2.PICC_HaltA();
    rfid2.PCD_StopCrypto1();
    delay(1000);
  }
}

void printUID(MFRC522 &reader) {
  for (byte i = 0; i < reader.uid.size; i++) {
    Serial.print(reader.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(reader.uid.uidByte[i], HEX);
  }
  Serial.println();
}
