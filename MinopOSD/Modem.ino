
#ifdef SOFT_MODEM
    char modemdata[60];
    static int XOR;
    int stringlength=0;
    int ichar=0;


void modemSend() {

    if (osd_fix_type==3) {
      //generate telemetry sequence
      prepare_array();
      //send_array();
      for (int i = 0; i<=stringlength; i++ ) {
        modem.write(modemdata[i]);
      }
    }
}

void prepare_array(){
int c;
String string_xor=0;

//protocol:  $PAK,1180000000,320000000,1500,0AFF
String  stringOne = "$PAK";
        stringOne += ",";
        stringOne += int(osd_lat*10000000);
        stringOne += ",";
        stringOne += int(osd_lon*10000000);
        stringOne += ",";
#ifdef REVO_ADD_ONS
	stringOne += (int)round(revo_baro_alt);
#else					
        stringOne += (int)round(osd_alt);
#endif
        stringOne += ",";   
        stringOne += osd_satellites_visible;
        stringOne += ",";
        stringOne += osd_fix_type;
        stringOne += ",";
        stringOne += (int16_t)round(osd_groundspeed);
        stringlength=stringOne.length() ;
            
        // Serial.println(stringOne);
         stringOne.toCharArray(modemdata, 50) ;
         for (XOR = 0, ichar = 0; ichar < strlen(modemdata); ichar++) {
           //Serial.print(modem[ichar]);
          c = (unsigned char)modemdata[ichar];
          if (c != ',') XOR ^= c;
         }
       // Serial.println("");
         stringOne += "*";
         string_xor= String(XOR, HEX);
         stringOne += string_xor;
         //stringOne += XOR;
         stringlength=stringOne.length();
         //Serial.println(stringOne);
         stringOne.toCharArray(modemdata, 50);
         
}

#endif 
