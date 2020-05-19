*** Settings ***
Test Setup        Initialize Server and Client
Test Teardown     Terminate Client and Server
Test Timeout      30
Library           OperatingSystem
Library           Process
Library           HttpCtrl.Server

*** Variables ***
${SATNOGS_API_TOKEN}    1234567890
${SATNOGS_NETWORK_API_URL}    http://127.0.0.1:52342/
${SATNOGS_STATION_ID}    123
${SATNOGS_STATION_LAT}    10
${SATNOGS_STATION_LON}    20
${SATNOGS_STATION_ELEV}    123
${SATNOGS_SOAPY_RX_DEVICE}    driver=rtlsdr
${SATNOGS_RX_SAMP_RATE}    2.048e6
${SATNOGS_ANTENNA}    RX
${SATNOGS_LOG_LEVEL}    DEBUG
${SATNOGS_NETWORK_API_QUERY_INTERVAL}    1

*** Test Cases ***
Run SatNOGS Client
    ${Result} =    Wait For Process    handle=satnogsclient    timeout=10 seconds    on_timeout=terminate
    Wait Until Keyword Succeeds    10 seconds    1 second    Process Should Be Stopped
    Should Be Equal As Integers    ${Result.rc}    -15

HTTP Server Based Test
    Wait For Request
    Reply By    200

*** Keywords ***
Start SatNOGS Client
    Set Environment Variable    SATNOGS_API_TOKEN    ${SATNOGS_API_TOKEN}
    Set Environment Variable    SATNOGS_NETWORK_API_URL    ${SATNOGS_NETWORK_API_URL}
    Set Environment Variable    SATNOGS_STATION_ID    ${SATNOGS_STATION_ID}
    Set Environment Variable    SATNOGS_STATION_LAT    ${SATNOGS_STATION_LAT}
    Set Environment Variable    SATNOGS_STATION_LON    ${SATNOGS_STATION_LON}
    Set Environment Variable    SATNOGS_STATION_ELEV    ${SATNOGS_STATION_ELEV}
    Set Environment Variable    SATNOGS_SOAPY_RX_DEVICE    ${SATNOGS_SOAPY_RX_DEVICE}
    Set Environment Variable    SATNOGS_RX_SAMP_RATE    ${SATNOGS_RX_SAMP_RATE}
    Set Environment Variable    SATNOGS_ANTENNA    ${SATNOGS_ANTENNA}
    Set Environment Variable    SATNOGS_LOG_LEVEL    ${SATNOGS_LOG_LEVEL}
    Set Environment Variable    SATNOGS_NETWORK_API_QUERY_INTERVAL    ${SATNOGS_NETWORK_API_QUERY_INTERVAL}
    Start Process    satnogs-client    shell=True    alias=satnogsclient

Initialize Server and Client
    Start Server    127.0.0.1    52342
    Start SatNOGS Client

Terminate Client and Server
    ${result} =    Terminate Process    handle=satnogsclient
    Log Many    stdout: ${result.stdout}    stderr: ${result.stderr}
    Stop Server
