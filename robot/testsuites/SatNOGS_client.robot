*** Settings ***
Library           OperatingSystem
Library           Process

*** Test Cases ***
Run SatNOGS Client
    Set Environment Variable    SATNOGS_API_TOKEN    1234567890
    Set Environment Variable    SATNOGS_NETWORK_API_URL    http://localhost:52342/
    Set Environment Variable    SATNOGS_STATION_ID    123
    Set Environment Variable    SATNOGS_STATION_LAT    10
    Set Environment Variable    SATNOGS_STATION_LON    20
    Set Environment Variable    SATNOGS_STATION_ELEV    123
    Set Environment Variable    SATNOGS_SOAPY_RX_DEVICE    driver=rtlsdr
    Set Environment Variable    SATNOGS_RX_SAMP_RATE    2.048e6
    Set Environment Variable    SATNOGS_LOG_LEVEL    DEBUG
    Start Process    satnogs-client    shell=True
    ${Result} =    Wait For Process    timeout=10 seconds    on_timeout=terminate
    Wait Until Keyword Succeeds    10 seconds    1 second    Process Should Be Stopped
    Should Be Equal As Integers    ${Result.rc}    -15
