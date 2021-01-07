Feature: wifi-setup-prompts

  Scenario: Test screens
    Given an english speaking user
     When the user says "test wifi connect setup screens"
     Then "wifi-connect" should reply with dialog from "1_ap.created_speech.dialog"
