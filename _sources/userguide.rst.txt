Kurzanleitung
=============

Grundfunktionen
---------------

Die Hauptaufgabe des Bots ist es, den Vorstand daran zu erinnern, wer fegen muss. Dafür schickt er jeden Dienstag um 20:30 Uhr eine Nachricht an alle dafür registriertern Telegram-Gruppen (mehr dazu unten).

Die Info kann auch manuell über den Befehl ``/fegen`` abgerufen werden.

Proben Pausieren
----------------

Es gibt zwei Arten, dem Bot mitzuteilen, dass die Proben pausiert sind:

1. Über den Befehl ``/proben_aussetzen`` können einzelne Wochen pausiert (oder ent-pausiert) werden. An den entsprechenden Dienstagen schickt der Bot keine Nachricht.
2. Über den Befehl ``/pausieren_umschalten`` werden Proben auf unbestimmte Zeit pausiert. Wird der Befehl ``/pausieren_umschalten`` erneut benutzt, werden die Problem fortgesetzt.

   .. note::
      Wochen, die über den Befehle ``/proben_aussezten`` pausiert wurden, *bleiben* in diesem Fall weiterhin pausiert!

Reihenfolge anpassen
--------------------

Ist mal etwas schief gegangen, kann die Reihenfolge der Register über den Befehl ``/setze_naechsten`` angpasst werden. In der nächsten Woche ist dann das ausgewählte Register an der Reihe. Danach geht es mit dem entsprechend nächsten Register weiter.

Zugriffsrechte
--------------

Rollen
######

Es gibt zwei Arten von Zugriffsrechten:

1. Admins. Diese Rolle ist für den Vorstand vorgesehen. Admins können Zugriffsrechte beliebig ändern, Proben pausieren, den Befehl ``/fegen`` ausführen und Gruppen registrieren/entfernen.
2. Zuschauer. Nutzer und Gruppen in dieser Rolle können *nur* den Befehl ``/fegen`` ausführen. Gruppen in dieser Rolle erhalten außerdem die wöchentliche Nachricht.

Sämtliche Nuzter können über den Befehl ``/nutzer_anzeigen`` angezeigt werden.

Gruppen für wöchentliche Nachricht registrieren
###############################################

Damit in einer Telegram-Gruppe die wöchentliche Nachricht erhält, sind zwei Schritte nötig:

1. Der Bot muss der Gruppe hinzugefügt werden.
2. Ein Admin muss in der Gruppe den Befehl ``/gruppenrechte_aendern`` ausführen.

Damit die Gruppe die wöchentliche Nachricht nicht mehr erhält, muss der Befehl ``/gruppenrechte_aendern`` erneut von einem Admin ausgeführt werden. Anschließend kann der Bot aus der Gruppe entfernt werden. Alternativ können Admins die Zuschauer-Gruppen auch wie folgt verwalten:

Zugriffsrechte verwalten
########################

Um Nutzer als Admins/Zuschauer hinzuzufügen oder Nutzer/Gruppen als Admin oder Zuschauer zu entfernen stehen die Befehle ``/nutzer_hinzufuegen`` und ``/nutzer_entfernen`` zur Verfügung. Sie können nur von Admins benutzt werden.




