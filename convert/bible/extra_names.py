"""Book names in the languages of the added editions, for works/bible/manifest.json `aliases`.

Two sources:
  * SOURCED: names read from the source files themselves at conversion time (Zefania <BIBLEBOOK bname>,
    USFX <h>, OSIS main titles, thiagobodruk `name` fields) — see collect_sourced() in convert_extra.py.
  * CURATED below: full book names for languages whose source files carry no native names (OSIS files
    from the Unbound Bible only have osisIDs; scrollmapper JSON only has English names).

Each curated entry is a ';'-separated list of 66 names in Protestant order (OT39 + NT27); the loader
asserts the count. Optional extra lists per language add deuterocanon or alternative spellings.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

P66 = C.CANONS['protestant-66']

CURATED66 = {
    'it': "Genesi;Esodo;Levitico;Numeri;Deuteronomio;Giosuè;Giudici;Rut;1 Samuele;2 Samuele;1 Re;2 Re;1 Cronache;2 Cronache;Esdra;Neemia;Ester;Giobbe;Salmi;Proverbi;Ecclesiaste;Cantico dei Cantici;Isaia;Geremia;Lamentazioni;Ezechiele;Daniele;Osea;Gioele;Amos;Abdia;Giona;Michea;Nahum;Abacuc;Sofonia;Aggeo;Zaccaria;Malachia;Matteo;Marco;Luca;Giovanni;Atti;Romani;1 Corinzi;2 Corinzi;Galati;Efesini;Filippesi;Colossesi;1 Tessalonicesi;2 Tessalonicesi;1 Timoteo;2 Timoteo;Tito;Filemone;Ebrei;Giacomo;1 Pietro;2 Pietro;1 Giovanni;2 Giovanni;3 Giovanni;Giuda;Apocalisse",
    'ko': "창세기;출애굽기;레위기;민수기;신명기;여호수아;사사기;룻기;사무엘상;사무엘하;열왕기상;열왕기하;역대상;역대하;에스라;느헤미야;에스더;욥기;시편;잠언;전도서;아가;이사야;예레미야;예레미야애가;에스겔;다니엘;호세아;요엘;아모스;오바댜;요나;미가;나훔;하박국;스바냐;학개;스가랴;말라기;마태복음;마가복음;누가복음;요한복음;사도행전;로마서;고린도전서;고린도후서;갈라디아서;에베소서;빌립보서;골로새서;데살로니가전서;데살로니가후서;디모데전서;디모데후서;디도서;빌레몬서;히브리서;야고보서;베드로전서;베드로후서;요한일서;요한이서;요한삼서;유다서;요한계시록",
    'el': "Γένεσις;Έξοδος;Λευιτικόν;Αριθμοί;Δευτερονόμιον;Ιησούς του Ναυή;Κριταί;Ρουθ;Α΄ Σαμουήλ;Β΄ Σαμουήλ;Α΄ Βασιλέων;Β΄ Βασιλέων;Α΄ Χρονικών;Β΄ Χρονικών;Έσδρας;Νεεμίας;Εσθήρ;Ιώβ;Ψαλμοί;Παροιμίαι;Εκκλησιαστής;Άσμα Ασμάτων;Ησαΐας;Ιερεμίας;Θρήνοι;Ιεζεκιήλ;Δανιήλ;Ωσηέ;Ιωήλ;Αμώς;Αβδιού;Ιωνάς;Μιχαίας;Ναούμ;Αββακούμ;Σοφονίας;Αγγαίος;Ζαχαρίας;Μαλαχίας;Κατά Ματθαίον;Κατά Μάρκον;Κατά Λουκάν;Κατά Ιωάννην;Πράξεις;Προς Ρωμαίους;Α΄ Κορινθίους;Β΄ Κορινθίους;Προς Γαλάτας;Προς Εφεσίους;Προς Φιλιππησίους;Προς Κολοσσαείς;Α΄ Θεσσαλονικείς;Β΄ Θεσσαλονικείς;Α΄ Τιμόθεον;Β΄ Τιμόθεον;Προς Τίτον;Προς Φιλήμονα;Προς Εβραίους;Ιακώβου;Α΄ Πέτρου;Β΄ Πέτρου;Α΄ Ιωάννου;Β΄ Ιωάννου;Γ΄ Ιωάννου;Ιούδα;Αποκάλυψις",
    'he': "בראשית;שמות;ויקרא;במדבר;דברים;יהושע;שופטים;רות;שמואל א;שמואל ב;מלכים א;מלכים ב;דברי הימים א;דברי הימים ב;עזרא;נחמיה;אסתר;איוב;תהלים;משלי;קהלת;שיר השירים;ישעיהו;ירמיהו;איכה;יחזקאל;דניאל;הושע;יואל;עמוס;עובדיה;יונה;מיכה;נחום;חבקוק;צפניה;חגי;זכריה;מלאכי;מתי;מרקוס;לוקס;יוחנן;מעשי השליחים;רומים;קורינתים א;קורינתים ב;גלטים;אפסים;פיליפים;קולוסים;תסלוניקים א;תסלוניקים ב;טימותיוס א;טימותיוס ב;טיטוס;פילימון;עברים;יעקב;פטרוס א;פטרוס ב;יוחנן א;יוחנן ב;יוחנן ג;יהודה;התגלות",
    'ar': "التكوين;الخروج;اللاويين;العدد;التثنية;يشوع;القضاة;راعوث;صموئيل الأول;صموئيل الثاني;الملوك الأول;الملوك الثاني;أخبار الأيام الأول;أخبار الأيام الثاني;عزرا;نحميا;أستير;أيوب;المزامير;الأمثال;الجامعة;نشيد الأنشاد;إشعياء;إرميا;مراثي إرميا;حزقيال;دانيال;هوشع;يوئيل;عاموس;عوبديا;يونان;ميخا;ناحوم;حبقوق;صفنيا;حجي;زكريا;ملاخي;متى;مرقس;لوقا;يوحنا;أعمال الرسل;رومية;كورنثوس الأولى;كورنثوس الثانية;غلاطية;أفسس;فيلبي;كولوسي;تسالونيكي الأولى;تسالونيكي الثانية;تيموثاوس الأولى;تيموثاوس الثانية;تيطس;فليمون;العبرانيين;يعقوب;بطرس الأولى;بطرس الثانية;يوحنا الأولى;يوحنا الثانية;يوحنا الثالثة;يهوذا;رؤيا يوحنا",
    'pl': "Rodzaju;Wyjścia;Kapłańska;Liczb;Powtórzonego Prawa;Jozuego;Sędziów;Rut;1 Samuela;2 Samuela;1 Królewska;2 Królewska;1 Kronik;2 Kronik;Ezdrasza;Nehemiasza;Estery;Hioba;Psalmów;Przysłów;Koheleta;Pieśń nad Pieśniami;Izajasza;Jeremiasza;Lamentacje;Ezechiela;Daniela;Ozeasza;Joela;Amosa;Abdiasza;Jonasza;Micheasza;Nahuma;Habakuka;Sofoniasza;Aggeusza;Zachariasza;Malachiasza;Mateusza;Marka;Łukasza;Jana;Dzieje Apostolskie;Rzymian;1 Koryntian;2 Koryntian;Galatów;Efezjan;Filipian;Kolosan;1 Tesaloniczan;2 Tesaloniczan;1 Tymoteusza;2 Tymoteusza;Tytusa;Filemona;Hebrajczyków;Jakuba;1 Piotra;2 Piotra;1 Jana;2 Jana;3 Jana;Judy;Apokalipsa",
    'sv': "Första Moseboken;Andra Moseboken;Tredje Moseboken;Fjärde Moseboken;Femte Moseboken;Josua;Domarboken;Rut;Första Samuelsboken;Andra Samuelsboken;Första Kungaboken;Andra Kungaboken;Första Krönikeboken;Andra Krönikeboken;Esra;Nehemja;Ester;Job;Psaltaren;Ordspråksboken;Predikaren;Höga Visan;Jesaja;Jeremia;Klagovisorna;Hesekiel;Daniel;Hosea;Joel;Amos;Obadja;Jona;Mika;Nahum;Habackuk;Sefanja;Haggai;Sakarja;Malaki;Matteus;Markus;Lukas;Johannes;Apostlagärningarna;Romarbrevet;Första Korintierbrevet;Andra Korintierbrevet;Galaterbrevet;Efesierbrevet;Filipperbrevet;Kolosserbrevet;Första Tessalonikerbrevet;Andra Tessalonikerbrevet;Första Timoteusbrevet;Andra Timoteusbrevet;Titusbrevet;Filemonbrevet;Hebreerbrevet;Jakobsbrevet;Första Petrusbrevet;Andra Petrusbrevet;Första Johannesbrevet;Andra Johannesbrevet;Tredje Johannesbrevet;Judasbrevet;Uppenbarelseboken",
    'nb': "Første Mosebok;Andre Mosebok;Tredje Mosebok;Fjerde Mosebok;Femte Mosebok;Josva;Dommerne;Rut;Første Samuelsbok;Andre Samuelsbok;Første Kongebok;Andre Kongebok;Første Krønikebok;Andre Krønikebok;Esra;Nehemja;Ester;Job;Salmene;Ordspråkene;Forkynneren;Høysangen;Jesaja;Jeremia;Klagesangene;Esekiel;Daniel;Hosea;Joel;Amos;Obadja;Jona;Mika;Nahum;Habakkuk;Sefanja;Haggai;Sakarja;Malaki;Matteus;Markus;Lukas;Johannes;Apostlenes gjerninger;Romerne;Første Korinterbrev;Andre Korinterbrev;Galaterne;Efeserne;Filipperne;Kolosserne;Første Tessalonikerbrev;Andre Tessalonikerbrev;Første Timoteusbrev;Andre Timoteusbrev;Titus;Filemon;Hebreerne;Jakob;Første Petersbrev;Andre Petersbrev;Første Johannesbrev;Andre Johannesbrev;Tredje Johannesbrev;Judas;Åpenbaringen",
    'da': "Første Mosebog;Anden Mosebog;Tredje Mosebog;Fjerde Mosebog;Femte Mosebog;Josva;Dommerbogen;Ruth;Første Samuelsbog;Anden Samuelsbog;Første Kongebog;Anden Kongebog;Første Krønikebog;Anden Krønikebog;Ezra;Nehemias;Ester;Job;Salmernes Bog;Ordsprogenes Bog;Prædikerens Bog;Højsangen;Esajas;Jeremias;Klagesangene;Ezekiel;Daniel;Hoseas;Joel;Amos;Obadias;Jonas;Mika;Nahum;Habakkuk;Zefanias;Haggaj;Zakarias;Malakias;Matthæus;Markus;Lukas;Johannes;Apostlenes Gerninger;Romerbrevet;Første Korintherbrev;Andet Korintherbrev;Galaterbrevet;Efeserbrevet;Filipperbrevet;Kolossenserbrevet;Første Thessalonikerbrev;Andet Thessalonikerbrev;Første Timotheusbrev;Andet Timotheusbrev;Titusbrevet;Filemonbrevet;Hebræerbrevet;Jakobs Brev;Første Petersbrev;Andet Petersbrev;Første Johannesbrev;Andet Johannesbrev;Tredje Johannesbrev;Judas' Brev;Johannes' Åbenbaring",
    'fi': "Ensimmäinen Mooseksen kirja;Toinen Mooseksen kirja;Kolmas Mooseksen kirja;Neljäs Mooseksen kirja;Viides Mooseksen kirja;Joosua;Tuomarien kirja;Ruut;Ensimmäinen Samuelin kirja;Toinen Samuelin kirja;Ensimmäinen kuningasten kirja;Toinen kuningasten kirja;Ensimmäinen aikakirja;Toinen aikakirja;Esra;Nehemia;Ester;Job;Psalmit;Sananlaskut;Saarnaaja;Laulujen laulu;Jesaja;Jeremia;Valitusvirret;Hesekiel;Daniel;Hoosea;Joel;Aamos;Obadja;Joona;Miika;Naahum;Habakuk;Sefanja;Haggai;Sakarja;Malakia;Matteus;Markus;Luukas;Johannes;Apostolien teot;Roomalaiskirje;Ensimmäinen korinttilaiskirje;Toinen korinttilaiskirje;Galatalaiskirje;Efesolaiskirje;Filippiläiskirje;Kolossalaiskirje;Ensimmäinen tessalonikalaiskirje;Toinen tessalonikalaiskirje;Ensimmäinen kirje Timoteukselle;Toinen kirje Timoteukselle;Kirje Titukselle;Kirje Filemonille;Heprealaiskirje;Jaakobin kirje;Ensimmäinen Pietarin kirje;Toinen Pietarin kirje;Ensimmäinen Johanneksen kirje;Toinen Johanneksen kirje;Kolmas Johanneksen kirje;Juudaksen kirje;Ilmestyskirja",
    'hu': "Teremtés;Kivonulás;Leviták;Számok;Második Törvénykönyv;Józsué;Bírák;Ruth;1 Sámuel;2 Sámuel;1 Királyok;2 Királyok;1 Krónikák;2 Krónikák;Ezsdrás;Nehémiás;Eszter;Jób;Zsoltárok;Példabeszédek;Prédikátor;Énekek éneke;Ézsaiás;Jeremiás;Siralmak;Ezékiel;Dániel;Hóseás;Jóel;Ámós;Abdiás;Jónás;Mikeás;Náhum;Habakuk;Zofóniás;Haggeus;Zakariás;Malakiás;Máté;Márk;Lukács;János;Apostolok cselekedetei;Rómaiakhoz;1 Korinthus;2 Korinthus;Galatákhoz;Efézusiakhoz;Filippiekhez;Kolosséiakhoz;1 Thesszalonika;2 Thesszalonika;1 Timóteus;2 Timóteus;Titusz;Filemon;Zsidókhoz;Jakab;1 Péter;2 Péter;1 János;2 János;3 János;Júdás;Jelenések",
    'vi': "Sáng Thế Ký;Xuất Ê-díp-tô Ký;Lê-vi Ký;Dân Số Ký;Phục Truyền Luật Lệ Ký;Giô-suê;Các Quan Xét;Ru-tơ;1 Sa-mu-ên;2 Sa-mu-ên;1 Các Vua;2 Các Vua;1 Sử Ký;2 Sử Ký;E-xơ-ra;Nê-hê-mi;Ê-xơ-tê;Gióp;Thi Thiên;Châm Ngôn;Truyền Đạo;Nhã Ca;Ê-sai;Giê-rê-mi;Ca Thương;Ê-xê-chi-ên;Đa-ni-ên;Ô-sê;Giô-ên;A-mốt;Áp-đia;Giô-na;Mi-chê;Na-hum;Ha-ba-cúc;Sô-phô-ni;A-ghê;Xa-cha-ri;Ma-la-chi;Ma-thi-ơ;Mác;Lu-ca;Giăng;Công Vụ Các Sứ Đồ;Rô-ma;1 Cô-rinh-tô;2 Cô-rinh-tô;Ga-la-ti;Ê-phê-sô;Phi-líp;Cô-lô-se;1 Tê-sa-lô-ni-ca;2 Tê-sa-lô-ni-ca;1 Ti-mô-thê;2 Ti-mô-thê;Tít;Phi-lê-môn;Hê-bơ-rơ;Gia-cơ;1 Phi-e-rơ;2 Phi-e-rơ;1 Giăng;2 Giăng;3 Giăng;Giu-đe;Khải Huyền",
    'uk': "Буття;Вихід;Левит;Числа;Повторення Закону;Ісус Навин;Суддів;Рут;1 Самуїла;2 Самуїла;1 Царів;2 Царів;1 Хронік;2 Хронік;Ездра;Неемія;Естер;Йов;Псалми;Приповісті;Екклезіяст;Пісня над піснями;Ісая;Єремія;Плач Єремії;Єзекіїль;Даниїл;Осія;Йоіл;Амос;Овдій;Йона;Михей;Наум;Авакум;Софонія;Огій;Захарія;Малахія;Матвія;Марка;Луки;Івана;Дії;Римлян;1 Коринтян;2 Коринтян;Галатів;Ефесян;Филип'ян;Колосян;1 Солунян;2 Солунян;1 Тимофія;2 Тимофія;Тита;Филимона;Євреїв;Якова;1 Петра;2 Петра;1 Івана;2 Івана;3 Івана;Юди;Об'явлення",
    'tr': "Yaratılış;Mısır'dan Çıkış;Levililer;Çölde Sayım;Yasa'nın Tekrarı;Yeşu;Hakimler;Rut;1 Samuel;2 Samuel;1 Krallar;2 Krallar;1 Tarihler;2 Tarihler;Ezra;Nehemya;Ester;Eyüp;Mezmurlar;Süleyman'ın Özdeyişleri;Vaiz;Ezgiler Ezgisi;Yeşaya;Yeremya;Ağıtlar;Hezekiel;Daniel;Hoşea;Yoel;Amos;Ovadya;Yunus;Mika;Nahum;Habakkuk;Sefanya;Hagay;Zekeriya;Malaki;Matta;Markos;Luka;Yuhanna;Elçilerin İşleri;Romalılar;1 Korintliler;2 Korintliler;Galatyalılar;Efesliler;Filipililer;Koloseliler;1 Selanikliler;2 Selanikliler;1 Timoteos;2 Timoteos;Titus;Filimon;İbraniler;Yakup;1 Petrus;2 Petrus;1 Yuhanna;2 Yuhanna;3 Yuhanna;Yahuda;Vahiy",
    'hr': "Postanak;Izlazak;Levitski zakonik;Brojevi;Ponovljeni zakon;Jošua;Suci;Ruta;1 Samuelova;2 Samuelova;1 Kraljevima;2 Kraljevima;1 Ljetopisa;2 Ljetopisa;Ezra;Nehemija;Estera;Job;Psalmi;Mudre izreke;Propovjednik;Pjesma nad pjesmama;Izaija;Jeremija;Tužaljke;Ezekiel;Daniel;Hošea;Joel;Amos;Obadija;Jona;Mihej;Nahum;Habakuk;Sefanija;Hagaj;Zaharija;Malahija;Matej;Marko;Luka;Ivan;Djela apostolska;Rimljanima;1 Korinćanima;2 Korinćanima;Galaćanima;Efežanima;Filipljanima;Kološanima;1 Solunjanima;2 Solunjanima;1 Timoteju;2 Timoteju;Titu;Filemonu;Hebrejima;Jakovljeva;1 Petrova;2 Petrova;1 Ivanova;2 Ivanova;3 Ivanova;Judina;Otkrivenje",
    'sr': "Постање;Излазак;Левитска;Бројеви;Поновљени закони;Исус Навин;Судије;Рута;1 Самуилова;2 Самуилова;1 Царевима;2 Царевима;1 Дневника;2 Дневника;Јездра;Немија;Јестира;Јов;Псалми;Приче Соломунове;Проповедник;Песма над песмама;Исаија;Јеремија;Плач Јеремијин;Језекиљ;Данило;Осија;Јоил;Амос;Авдија;Јона;Михеј;Наум;Авакум;Софонија;Агеј;Захарија;Малахија;Матеј;Марко;Лука;Јован;Дела апостолска;Римљанима;1 Коринћанима;2 Коринћанима;Галатима;Ефесцима;Филипљанима;Колошанима;1 Солуњанима;2 Солуњанима;1 Тимотеју;2 Тимотеју;Титу;Филимону;Јеврејима;Јаковљева;1 Петрова;2 Петрова;1 Јованова;2 Јованова;3 Јованова;Јудина;Откривење",
    'tl': "Genesis;Exodo;Levitico;Mga Bilang;Deuteronomio;Josue;Mga Hukom;Ruth;1 Samuel;2 Samuel;1 Mga Hari;2 Mga Hari;1 Mga Cronica;2 Mga Cronica;Ezra;Nehemias;Esther;Job;Mga Awit;Mga Kawikaan;Eclesiastes;Awit ng mga Awit;Isaias;Jeremias;Mga Panaghoy;Ezekiel;Daniel;Oseas;Joel;Amos;Obadias;Jonas;Mikas;Nahum;Habacuc;Zefanias;Hagai;Zacarias;Malakias;Mateo;Marcos;Lucas;Juan;Mga Gawa;Mga Taga-Roma;1 Mga Taga-Corinto;2 Mga Taga-Corinto;Mga Taga-Galacia;Mga Taga-Efeso;Mga Taga-Filipos;Mga Taga-Colosas;1 Mga Taga-Tesalonica;2 Mga Taga-Tesalonica;1 Timoteo;2 Timoteo;Tito;Filemon;Mga Hebreo;Santiago;1 Pedro;2 Pedro;1 Juan;2 Juan;3 Juan;Judas;Pahayag",
    'th': "ปฐมกาล;อพยพ;เลวีนิติ;กันดารวิถี;เฉลยธรรมบัญญัติ;โยชูวา;ผู้วินิจฉัย;นางรูธ;1 ซามูเอล;2 ซามูเอล;1 พงศ์กษัตริย์;2 พงศ์กษัตริย์;1 พงศาวดาร;2 พงศาวดาร;เอสรา;เนหะมีย์;เอสเธอร์;โยบ;สดุดี;สุภาษิต;ปัญญาจารย์;เพลงซาโลมอน;อิสยาห์;เยเรมีย์;เพลงคร่ำครวญ;เอเสเคียล;ดาเนียล;โฮเชยา;โยเอล;อาโมส;โอบาดีย์;โยนาห์;มีคาห์;นาฮูม;ฮาบากุก;เศฟันยาห์;ฮักกัย;เศคาริยาห์;มาลาคี;มัทธิว;มาระโก;ลูกา;ยอห์น;กิจการ;โรม;1 โครินธ์;2 โครินธ์;กาลาเทีย;เอเฟซัส;ฟีลิปปี;โคโลสี;1 เธสะโลนิกา;2 เธสะโลนิกา;1 ทิโมธี;2 ทิโมธี;ทิตัส;ฟีเลโมน;ฮีบรู;ยากอบ;1 เปโตร;2 เปโตร;1 ยอห์น;2 ยอห์น;3 ยอห์น;ยูดา;วิวรณ์",
    'ja': "創世記;出エジプト記;レビ記;民数記;申命記;ヨシュア記;士師記;ルツ記;サムエル記上;サムエル記下;列王紀上;列王紀下;歴代志上;歴代志下;エズラ記;ネヘミヤ記;エステル記;ヨブ記;詩篇;箴言;伝道の書;雅歌;イザヤ書;エレミヤ書;哀歌;エゼキエル書;ダニエル書;ホセア書;ヨエル書;アモス書;オバデヤ書;ヨナ書;ミカ書;ナホム書;ハバクク書;ゼパニヤ書;ハガイ書;ゼカリヤ書;マラキ書;マタイ;マルコ;ルカ;ヨハネ;使徒行伝;ローマ;コリント第一;コリント第二;ガラテヤ;エペソ;ピリピ;コロサイ;テサロニケ第一;テサロニケ第二;テモテ第一;テモテ第二;テトス;ピレモン;ヘブル;ヤコブ;ペテロ第一;ペテロ第二;ヨハネ第一;ヨハネ第二;ヨハネ第三;ユダ;黙示録",
    'ru': "Бытие;Исход;Левит;Числа;Второзаконие;Иисус Навин;Судьи;Руфь;1 Царств;2 Царств;3 Царств;4 Царств;1 Паралипоменон;2 Паралипоменон;Ездра;Неемия;Есфирь;Иов;Псалтирь;Притчи;Екклесиаст;Песнь Песней;Исаия;Иеремия;Плач Иеремии;Иезекииль;Даниил;Осия;Иоиль;Амос;Авдий;Иона;Михей;Наум;Аввакум;Софония;Аггей;Захария;Малахия;От Матфея;От Марка;От Луки;От Иоанна;Деяния;Римлянам;1 Коринфянам;2 Коринфянам;Галатам;Ефесянам;Филиппийцам;Колоссянам;1 Фессалоникийцам;2 Фессалоникийцам;1 Тимофею;2 Тимофею;Титу;Филимону;Евреям;Иакова;1 Петра;2 Петра;1 Иоанна;2 Иоанна;3 Иоанна;Иуды;Откровение",
    'pt': "Gênesis;Êxodo;Levítico;Números;Deuteronômio;Josué;Juízes;Rute;1 Samuel;2 Samuel;1 Reis;2 Reis;1 Crônicas;2 Crônicas;Esdras;Neemias;Ester;Jó;Salmos;Provérbios;Eclesiastes;Cântico dos Cânticos;Isaías;Jeremias;Lamentações;Ezequiel;Daniel;Oseias;Joel;Amós;Obadias;Jonas;Miqueias;Naum;Habacuque;Sofonias;Ageu;Zacarias;Malaquias;Mateus;Marcos;Lucas;João;Atos;Romanos;1 Coríntios;2 Coríntios;Gálatas;Efésios;Filipenses;Colossenses;1 Tessalonicenses;2 Tessalonicenses;1 Timóteo;2 Timóteo;Tito;Filemom;Hebreus;Tiago;1 Pedro;2 Pedro;1 João;2 João;3 João;Judas;Apocalipse",
    'nl': "Genesis;Exodus;Leviticus;Numeri;Deuteronomium;Jozua;Richteren;Ruth;1 Samuël;2 Samuël;1 Koningen;2 Koningen;1 Kronieken;2 Kronieken;Ezra;Nehemia;Esther;Job;Psalmen;Spreuken;Prediker;Hooglied;Jesaja;Jeremia;Klaagliederen;Ezechiël;Daniël;Hosea;Joël;Amos;Obadja;Jona;Micha;Nahum;Habakuk;Zefanja;Haggai;Zacharia;Maleachi;Mattheüs;Markus;Lukas;Johannes;Handelingen;Romeinen;1 Korinthe;2 Korinthe;Galaten;Efeze;Filippenzen;Kolossenzen;1 Thessalonicenzen;2 Thessalonicenzen;1 Timotheüs;2 Timotheüs;Titus;Filemon;Hebreeën;Jakobus;1 Petrus;2 Petrus;1 Johannes;2 Johannes;3 Johannes;Judas;Openbaring",
    'cs': "Genesis;Exodus;Leviticus;Numeri;Deuteronomium;Jozue;Soudců;Rút;1 Samuelova;2 Samuelova;1 Královská;2 Královská;1 Paralipomenon;2 Paralipomenon;Ezdráš;Nehemjáš;Ester;Jób;Žalmy;Přísloví;Kazatel;Píseň písní;Izajáš;Jeremjáš;Pláč;Ezechiel;Daniel;Ozeáš;Jóel;Ámos;Abdijáš;Jonáš;Micheáš;Nahum;Abakuk;Sofonjáš;Ageus;Zacharjáš;Malachiáš;Matouš;Marek;Lukáš;Jan;Skutky;Římanům;1 Korintským;2 Korintským;Galatským;Efezským;Filipským;Koloským;1 Tesalonickým;2 Tesalonickým;1 Timoteovi;2 Timoteovi;Titovi;Filemonovi;Židům;Jakub;1 Petrova;2 Petrova;1 Janova;2 Janova;3 Janova;Judova;Zjevení",
    'ro': "Geneza;Exodul;Leviticul;Numeri;Deuteronomul;Iosua;Judecătorii;Rut;1 Samuel;2 Samuel;1 Împărați;2 Împărați;1 Cronici;2 Cronici;Ezra;Neemia;Estera;Iov;Psalmii;Proverbele;Eclesiastul;Cântarea Cântărilor;Isaia;Ieremia;Plângerile;Ezechiel;Daniel;Osea;Ioel;Amos;Obadia;Iona;Mica;Naum;Habacuc;Țefania;Hagai;Zaharia;Maleahi;Matei;Marcu;Luca;Ioan;Faptele Apostolilor;Romani;1 Corinteni;2 Corinteni;Galateni;Efeseni;Filipeni;Coloseni;1 Tesaloniceni;2 Tesaloniceni;1 Timotei;2 Timotei;Tit;Filimon;Evrei;Iacov;1 Petru;2 Petru;1 Ioan;2 Ioan;3 Ioan;Iuda;Apocalipsa",
    'sw': "Mwanzo;Kutoka;Mambo ya Walawi;Hesabu;Kumbukumbu la Torati;Yoshua;Waamuzi;Ruthu;1 Samweli;2 Samweli;1 Wafalme;2 Wafalme;1 Mambo ya Nyakati;2 Mambo ya Nyakati;Ezra;Nehemia;Esta;Ayubu;Zaburi;Mithali;Mhubiri;Wimbo Ulio Bora;Isaya;Yeremia;Maombolezo;Ezekieli;Danieli;Hosea;Yoeli;Amosi;Obadia;Yona;Mika;Nahumu;Habakuki;Sefania;Hagai;Zekaria;Malaki;Mathayo;Marko;Luka;Yohana;Matendo ya Mitume;Warumi;1 Wakorintho;2 Wakorintho;Wagalatia;Waefeso;Wafilipi;Wakolosai;1 Wathesalonike;2 Wathesalonike;1 Timotheo;2 Timotheo;Tito;Filemoni;Waebrania;Yakobo;1 Petro;2 Petro;1 Yohana;2 Yohana;3 Yohana;Yuda;Ufunuo",
    'hi': "उत्पत्ति;निर्गमन;लैव्यव्यवस्था;गिनती;व्यवस्थाविवरण;यहोशू;न्यायियों;रूत;1 शमूएल;2 शमूएल;1 राजा;2 राजा;1 इतिहास;2 इतिहास;एज्रा;नहेम्याह;एस्तेर;अय्यूब;भजन संहिता;नीतिवचन;सभोपदेशक;श्रेष्ठगीत;यशायाह;यिर्मयाह;विलापगीत;यहेजकेल;दानिय्येल;होशे;योएल;आमोस;ओबद्याह;योना;मीका;नहूम;हबक्कूक;सपन्याह;हाग्गै;जकर्याह;मलाकी;मत्ती;मरकुस;लूका;यूहन्ना;प्रेरितों के काम;रोमियों;1 कुरिन्थियों;2 कुरिन्थियों;गलातियों;इफिसियों;फिलिप्पियों;कुलुस्सियों;1 थिस्सलुनीकियों;2 थिस्सलुनीकियों;1 तीमुथियुस;2 तीमुथियुस;तीतुस;फिलेमोन;इब्रानियों;याकूब;1 पतरस;2 पतरस;1 यूहन्ना;2 यूहन्ना;3 यूहन्ना;यहूदा;प्रकाशितवाक्य",
}

# Extra alternates per language, code -> names
CURATED_EXTRA = {
    'it': {'tob': ['Tobia'], 'jdt': ['Giuditta'], 'wis': ['Sapienza'], 'sir': ['Siracide'], 'bar': ['Baruc'],
           '1ma': ['1 Maccabei'], '2ma': ['2 Maccabei'], 'sng': ['Cantico'], 'act': ['Atti degli Apostoli'],
           'rev': ['Rivelazione']},
    'pt': {'tob': ['Tobias'], 'jdt': ['Judite'], 'wis': ['Sabedoria'], 'sir': ['Eclesiástico'], 'bar': ['Baruc'],
           '1ma': ['1 Macabeus'], '2ma': ['2 Macabeus'], 'sng': ['Cantares', 'Cânticos'], 'hos': ['Oséias'],
           'mic': ['Miquéias'], 'lam': ['Lamentações de Jeremias'],
           'gen': ['Gn'], 'exo': ['Êx'], 'psa': ['Sl'], 'jhn': ['Jo'], 'rev': ['Ap'], 'act': ['Atos dos Apóstolos', 'At']},
    'nl': {'tob': ['Tobit', 'Tobias'], 'jdt': ['Judit'], 'wis': ['Wijsheid'], 'sir': ['Sirach', 'Jezus Sirach'],
           'bar': ['Baruch'], '1ma': ['1 Makkabeeën'], '2ma': ['2 Makkabeeën'], '1co': ['1 Korinthiërs'],
           '2co': ['2 Korinthiërs'], 'eph': ['Efeziërs'], 'mat': ['Mattheus', 'Matteüs'], 'act': ['Handelingen der apostelen']},
    'ru': {'tob': ['Товит'], 'jdt': ['Иудифь'], 'wis': ['Премудрость Соломона'], 'sir': ['Сирах', 'Премудрость Иисуса, сына Сирахова'],
           'bar': ['Варух'], '1ma': ['1 Маккавейская'], '2ma': ['2 Маккавейская'], '3ma': ['3 Маккавейская'],
           '1es': ['2 Ездры'], '2es': ['3 Ездры'], 'lje': ['Послание Иеремии'], 'man': ['Молитва Манассии'],
           '1sa': ['1 Самуила'], '2sa': ['2 Самуила'], 'mat': ['Матфея'], 'mrk': ['Марка'], 'luk': ['Луки'], 'jhn': ['Иоанна'],
           'act': ['Деяния апостолов'], 'rev': ['Апокалипсис']},
    'uk': {'tob': ['Товит'], 'jdt': ['Юдит'], 'wis': ['Мудрість'], 'sir': ['Сирах'], 'bar': ['Варух'],
           '1ma': ['1 Макавеїв'], '2ma': ['2 Макавеїв'], '3ma': ['3 Макавеїв'], 'rev': ['Одкровення']},
    'el': {'gen': ['Γένεση'], 'exo': ['Έξοδος'], 'deu': ['Δευτερονόμιο'], 'psa': ['Ψαλμός'], 'mat': ['Ματθαίος'],
           'mrk': ['Μάρκος'], 'luk': ['Λουκάς'], 'jhn': ['Ιωάννης'], 'act': ['Πράξεις των Αποστόλων'], 'rom': ['Ρωμαίους'],
           'rev': ['Αποκάλυψη']},
    'he': {'psa': ['תהילים'], 'sng': ['שיר השירים'], 'act': ['מעשי השליחים']},
    'zh': {'gen': ['创世记', '創世記'], 'psa': ['诗篇', '詩篇'], 'mat': ['马太福音', '馬太福音'], 'rev': ['启示录', '啟示錄'],
           'tob': ['多俾亞傳'], 'jdt': ['友弟德傳'], 'wis': ['智慧篇'], 'sir': ['德訓篇'], 'bar': ['巴路克'], '1ma': ['瑪加伯上'], '2ma': ['瑪加伯下']},
    'ko': {'gen': ['창세'], 'psa': ['시'], 'mat': ['마태', '마태복음서'], 'mrk': ['마가', '마르코'], 'luk': ['누가'], 'jhn': ['요한'],
           'rev': ['계시록', '요한묵시록']},
    'ja': {'mat': ['マタイによる福音書'], 'mrk': ['マルコによる福音書'], 'luk': ['ルカによる福音書'], 'jhn': ['ヨハネによる福音書'],
           'rev': ['ヨハネの黙示録'], 'psa': ['詩編']},
    'sv': {'gen': ['1 Mosebok', '1 Mos'], 'exo': ['2 Mosebok', '2 Mos'], 'lev': ['3 Mosebok', '3 Mos'], 'num': ['4 Mosebok', '4 Mos'],
           'deu': ['5 Mosebok', '5 Mos'], '1sa': ['1 Samuelsboken', '1 Sam'], '2sa': ['2 Samuelsboken', '2 Sam'],
           '1ki': ['1 Kungaboken', '1 Kung'], '2ki': ['2 Kungaboken', '2 Kung'], '1ch': ['1 Krönikeboken', '1 Krön'],
           '2ch': ['2 Krönikeboken', '2 Krön'], 'psa': ['Psalm'], 'rev': ['Uppenbarelsen']},
    'nb': {'gen': ['1 Mosebok', '1 Mos'], 'exo': ['2 Mosebok', '2 Mos'], 'lev': ['3 Mosebok', '3 Mos'], 'num': ['4 Mosebok', '4 Mos'],
           'deu': ['5 Mosebok', '5 Mos'], '1sa': ['1 Samuelsbok', '1 Sam'], '2sa': ['2 Samuelsbok', '2 Sam'], '1ki': ['1 Kongebok'],
           '2ki': ['2 Kongebok'], '1ch': ['1 Krønikebok'], '2ch': ['2 Krønikebok'], 'psa': ['Salmenes bok', 'Salme'],
           'act': ['Apostlenes gjerninger', 'Apg'], 'rev': ['Johannes' + "' åpenbaring"]},
    'da': {'gen': ['1 Mosebog', '1 Mos'], 'exo': ['2 Mosebog', '2 Mos'], 'lev': ['3 Mosebog', '3 Mos'], 'num': ['4 Mosebog', '4 Mos'],
           'deu': ['5 Mosebog', '5 Mos'], 'psa': ['Salmerne', 'Salme'], 'pro': ['Ordsprogene'], 'ecc': ['Prædikeren'],
           '1sa': ['1 Samuelsbog'], '2sa': ['2 Samuelsbog'], '1ki': ['1 Kongebog'], '2ki': ['2 Kongebog'], 'rev': ['Åbenbaringen']},
    'fi': {'gen': ['1 Mooseksen kirja', '1 Moos', '1. Mooseksen kirja'], 'exo': ['2 Mooseksen kirja', '2 Moos'], 'lev': ['3 Mooseksen kirja', '3 Moos'],
           'num': ['4 Mooseksen kirja', '4 Moos'], 'deu': ['5 Mooseksen kirja', '5 Moos'], '1sa': ['1 Samuelin kirja', '1 Sam'],
           '2sa': ['2 Samuelin kirja', '2 Sam'], '1ki': ['1 Kuningasten kirja', '1 Kun'], '2ki': ['2 Kuningasten kirja', '2 Kun'],
           '1ch': ['1 Aikakirja', '1 Aik'], '2ch': ['2 Aikakirja', '2 Aik'], 'jdg': ['Tuomarit'], 'rom': ['Roomalaisille'],
           '1co': ['1 Korinttilaisille', '1 Kor'], '2co': ['2 Korinttilaisille', '2 Kor'], 'gal': ['Galatalaisille'], 'eph': ['Efesolaisille'],
           'php': ['Filippiläisille'], 'col': ['Kolossalaisille'], '1th': ['1 Tessalonikalaisille', '1 Tess'], '2th': ['2 Tessalonikalaisille', '2 Tess'],
           '1ti': ['1 Timoteukselle', '1 Tim'], '2ti': ['2 Timoteukselle', '2 Tim'], 'tit': ['Titukselle'], 'phm': ['Filemonille'],
           'heb': ['Heprealaisille'], 'jas': ['Jaakob'], '1pe': ['1 Pietari'], '2pe': ['2 Pietari'], '1jn': ['1 Johannes'],
           '2jn': ['2 Johannes'], '3jn': ['3 Johannes'], 'jud': ['Juuda'], 'rev': ['Ilmestys', 'Johanneksen ilmestys']},
    'hu': {'gen': ['1 Mózes', 'Mózes I'], 'exo': ['2 Mózes', 'Mózes II'], 'lev': ['3 Mózes', 'Mózes III'], 'num': ['4 Mózes', 'Mózes IV'],
           'deu': ['5 Mózes', 'Mózes V'], 'rom': ['Róma'], '1co': ['1 Korinthus'], 'gal': ['Galata'], 'eph': ['Efézus'], 'php': ['Filippi'],
           'col': ['Kolossé'], 'heb': ['Zsidók'], 'rev': ['Jelenések könyve']},
    'pl': {'gen': ['Księga Rodzaju', '1 Mojżeszowa'], 'exo': ['Księga Wyjścia', '2 Mojżeszowa'], 'lev': ['Księga Kapłańska', '3 Mojżeszowa'],
           'num': ['Księga Liczb', '4 Mojżeszowa'], 'deu': ['Księga Powtórzonego Prawa', '5 Mojżeszowa'], 'psa': ['Psalmy', 'Księga Psalmów'],
           'ecc': ['Kaznodziei'], 'rev': ['Objawienie'], 'act': ['Dzieje']},
    'tr': {'act': ['Elçilerin İşleri', 'Elçiler'], 'rev': ['Esinleme']},
    'hr': {'tob': ['Tobija'], 'jdt': ['Judita'], 'wis': ['Mudrost'], 'sir': ['Sirah'], 'bar': ['Baruh'], '1ma': ['1 Makabejcima'], '2ma': ['2 Makabejcima']},
    'ar': {'psa': ['مزامير', 'مزمور'], 'gen': ['تكوين'], 'mat': ['إنجيل متى'], 'mrk': ['إنجيل مرقس'], 'luk': ['إنجيل لوقا'], 'jhn': ['إنجيل يوحنا'], 'rev': ['الرؤيا']},
    'vi': {'act': ['Công Vụ'], 'rev': ['Khải Thị']},
}

TITLES = {
    'it': 'La Bibbia', 'pt': 'A Bíblia', 'nl': 'De Bijbel', 'ru': 'Библия', 'uk': 'Біблія', 'pl': 'Biblia', 'cs': 'Bible',
    'sv': 'Bibeln', 'nb': 'Bibelen', 'da': 'Bibelen', 'fi': 'Raamattu', 'hu': 'Biblia', 'ro': 'Biblia', 'el': 'Η Αγία Γραφή',
    'he': 'התנ"ך', 'ar': 'الكتاب المقدس', 'zh': '聖經', 'ko': '성경', 'ja': '聖書', 'vi': 'Kinh Thánh', 'th': 'พระคัมภีร์',
    'tl': 'Ang Biblia', 'tr': 'Kutsal Kitap', 'hr': 'Biblija', 'sr': 'Библија', 'sw': 'Biblia', 'hi': 'बाइबिल',
}


def curated():
    """Return {code: [names]} merged across all curated languages."""
    out = {}
    for lang, s in CURATED66.items():
        names = [x.strip() for x in s.split(';')]
        assert len(names) == 66, (lang, len(names))
        for code, name in zip(P66, names):
            out.setdefault(code, []).append(name)
    for lang, d in CURATED_EXTRA.items():
        for code, names in d.items():
            out.setdefault(code, []).extend(names)
    return out
