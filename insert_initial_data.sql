INSERT INTO locations (id, city_name, latitude, longitude)
VALUES (1, 'Kraków', 50.06, 19.94)
ON CONFLICT (id) DO NOTHING;

INSERT INTO dict_weather_code (weather_code, description) VALUES
(0, 'Czyste niebo'),
(1, 'Głównie czyste niebo'),
(2, 'Częściowe zachmurzenie'),
(3, 'Całkowite zachmurzenie'),
(45, 'Mgła'),
(48, 'Mgła osadzająca szron'),
(51, 'Mżawka: lekka'),
(53, 'Mżawka: umiarkowana'),
(55, 'Mżawka: intensywna'),
(56, 'Marznąca mżawka: lekka'),
(57, 'Marznąca mżawka: intensywna'),
(61, 'Deszcz: słaby'),
(63, 'Deszcz: umiarkowany'),
(65, 'Deszcz: silny'),
(66, 'Marznący deszcz: lekki'),
(67, 'Marznący deszcz: silny'),
(71, 'Opady śniegu: słabe'),
(73, 'Opady śniegu: umiarkowane'),
(75, 'Opady śniegu: silne'),
(77, 'Ziarna lodowe'),
(80, 'Przelotny deszcz: słaby'),
(81, 'Przelotny deszcz: umiarkowany'),
(82, 'Przelotny deszcz: gwałtowny'),
(85, 'Przelotny śnieg: słaby'),
(86, 'Przelotny śnieg: silny'),
(95, 'Burza: o natężeniu słabym lub umiarkowanym'),
(96, 'Burza z gradem: lekka'),
(99, 'Burza z gradem: ciężka')
ON CONFLICT (weather_code) DO NOTHING;