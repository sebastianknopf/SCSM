# Einführung

Mit der Marktöffnung im ÖV-Sektor stehen Verkehrsunternehmen vielfach unter hohem Kostendruck. Besonders in eigenwirtschaftlich betriebenen Netzen ist die Einnahmeabsicherung ein wichtiges Instrument um die wirtschaftliche Stabilität des Verkehrsunternehmens sicherzustellen. Durch den vielfach praktizierten kontrollierten Vordereinstieg bei Bussen ist dies in der Regel nicht vollumfänglich zu leisten. Zusätzliches, besonders geschultes Kontrollpersonal führt allerdings zu Mehrkosten von nicht unerheblichem Umfang. Dem gegenüber stehen sowohl die Einnahmen aus dem verhängten erhöhten Beförderungsentgelt (EBE) und die Mehreinnahmen aus einem nachweislichen Rückgang der Fahrgeldhinterziehungsquote durch den Einsatz von gesondertem Kontrollpersonal. Ziel sollte es also sein, das Gesamtverlustsaldo aus der Fahrgeldhinterziehung so gering wie möglich zu halten.

In diesem Projekt wurde ein statistisches Modell zur optimierten Einteilung des Kontrollpersonals entwickelt. Dabei steht die Maximierung der EBE-Einnahmen und die gleichmäßige Verteilung der Kontrollen über alle Linien hinweg im Zentrum. Das Modell unter der Bezeichnung SCSM (für Statistics based Crew Scheduling Model) analysiert hierzu Daten aus den bisher geleisteten Fahrscheinkontrollen und ordnet jeder Dienststunde eine zu kontrollierende Linie zu. Das Projekt entstand im Rahmen des Master-Studiums Verkehrssystemmanagement am [Institut für ubiquitäre Mobilitätssysteme](https://www.h-ka.de/iums/profil) der [Hochschule Karlsruhe](https://www.h-ka.de).

## Arbeitsweise

SCSM verarbeitet eine Liste mit vorab geplanten Dienstzeiten. Zu jeder geplanten Stunde werden die Prioritäten der einzelnen Linien ermittelt und dann die Linien mit der höchsten Priorität verplant.

Die Priorität einer Linie hängt hauptsächlich von der Beanstandungsquote der Linie ab. An zweiter Stelle steht die gleichmäßige Verteilung der Kontrollen über alle Linien. Dadurch ist sichergestellt, dass Linien mit erfahrungsgemäß höherer Beanstandungsquote häufiger kontrolliert und andere Linien im Gegenzug auch nicht vernachlässigt werden. Essenziell für die Beurteilung der Stichprobenqualität ist eine aussagekräftige Stichprobe an kontrollierten Fahrgästen. Linien werden in Zeitfenster, in denen nach aktuellem Datenstand weniger als 50 Fahrgäste kontrolliert wurden, also generell höher priorisiert, um einen validen Stichprobenumfang sicherzustellen. Weitere Informationen zur exakten Priorisierung von Linien sind in der offiziellen Ausarbeitung [Paper_IUMS_2022.pdf](/Paper_IUMS_2022.pdf) zu finden.

## Beispielskript

Eine Beispielimplementierung, welche SCSM einsetzt, ist im Skript ```run.py``` zu finden. Um dieses Skript zu starten, wird nur 

* ein Beispieldatensatz als SQLite-Datenbank
* eine Datei mit geplanten Dienstzeiten mit mindestens einem geplanten Dienst

benötigt. Eine geeignete Beispieldatenbank im Repository enthalten.

Das Beispielskript kann mit Hilfe des Befehls

```
python run.py -d ./input/example_report_data.db3 -s ./input/example_schedule_data.txt
```

gestartet werden. Zum Ende der Ausführung wird das Ergebnis der Dienstplanung in einem Fenster angezeigt.

Mit Hilfe des Befehls ```python run.py -h``` werden Hinweise zum Aufruf des Beispielskriptes angezeigt.

## Linienauswahl

Wenn nur bestimmte Linien bei der Berechnung berücksichtigt werden sollen, kann die Option

```
-r 15,17,18,20,21
```

an den Aufruf angehängt werden. Die zu berücksichtigenden Linien sind durch Kommata getrennt anzugeben. Linien, die in dieser Liste dann nicht enthalten sind, werden im Rahmen der Dienstplanung dann auch nicht berücksichtigt.

## Eingangsdatenformat

Die SQLite-Datenbank mit den Eingangsdaten muss mindestens eine Tabelle mit der Bezeichnung ```report``` enthalten. Jede Zeile der Tabelle repräsentiert eine zurückgelegte Fahrt des Kontrollpersonals und muss die Spalten

* date: Datum im Format yyyyMMdd
* route_name: Eindeutige Linienbezeichnung
* departure_time: Abfahrtszeit der Fahrt im Format HH:mm:ss
* arrival_time: Ankunftszeit der Fahrt im Format HH:mm:ss
* num_passengers: Anzahl kontrollierter Fahrgäste während dieser Fahrt
* num_complaints: Anzahl Beanstandungen während dieser Fahrt

enthalten.

Die Datei mit den geplanten Diensten muss mindestens die Spalten

* date: Datum des Dienstes im Format yyyyMMdd
* start_hour: Stunde des Dienstbeginns (erster Fahrtbeginn ab hh:01)
* end_hour: Stunde des Dienstendes (letzter Fahrtbeginn bis hh:59 _in der vorhergehenden Stunde_!)

enthalten. Jede Stunde darf an einem Tag nur einmal verplant sein. Als Trennzeichen muss ein Semikolon verwendet werden.

## Lizenz

Dieses Projekt ist lizenziert unter der Apache 2.0 Lizenz. Weitere Informationen unter [LICENSE](/LICENSE.md).