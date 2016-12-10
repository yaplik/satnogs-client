import json
from datetime import datetime, timedelta

EPOCH_DATE = datetime.strptime('20000101T000000Z', '%Y%m%dT%H%M%SZ')


def wod_decode(hex_payload):
    payload = ''
    for index, part in enumerate(hex_payload):
        payload += ''.join(format(ord(x), 'b').zfill(8) for x in part)
    dt = payload[:32]
    datasets = payload[32:]

    # calculate initial datetime
    seconds = int(dt[24:] + dt[16:24] + dt[8:16] + dt[:8], 2)
    data = [{}]
    for i in range(0, len(datasets) / 57):
        sub_data = [{}]
        dataset = datasets[:57]
        datasets = datasets[57:]

        dataset_datetime = EPOCH_DATE + timedelta(seconds=seconds)
        seconds -= 60
        satellite_datetime = datetime.strftime(dataset_datetime, '%Y%m%dT%H%M%SZ')

        # mode
        status = dataset[0]

        # battery voltage
        u = float(int(dataset[1:9], 2))
        bat_v = round((u + 60) / 20, 2)

        # battery current
        u = float(int(dataset[9:17], 2))
        bat_c = round((u - 127) / 127, 2)

        # 3v3 current
        u = float(int(dataset[17:25], 2))
        v3_c = round(u / 40, 2)

        # 5v current
        u = float(int(dataset[25:33], 2))
        v5_c = round(u / 40, 2)

        # temperature comms
        u = float(int(dataset[33:41], 2))
        comms_t = round((u - 60) / 4, 2)

        # temperature eps
        u = float(int(dataset[41:49], 2))
        eps_t = round((u - 60) / 4, 2)

        # temperature battery
        u = float(int(dataset[49:], 2))
        batt_t = round((u - 60) / 4, 2)

        sub_data[0]['Sat Time'] = satellite_datetime
        sub_data[0]['Status'] = status
        sub_data[0]['VBAT'] = bat_v
        sub_data[0]['IBAT'] = bat_c
        sub_data[0]['I3V3'] = v3_c
        sub_data[0]['I5V0'] = v5_c
        sub_data[0]['TCOMMS'] = comms_t
        sub_data[0]['TEPS'] = eps_t
        sub_data[0]['TBAT'] = batt_t

        # data[0][i] = json.loads(json.dumps(sub_data, indent=2, sort_keys=True))
        data[0][i] = sub_data

    response = {}
    response['type'] = 'WOD'
    response['content'] = json.dumps(data, indent=2, sort_keys=True)
    return response


def obc_wod_decode(hex_payload):
    payload = ''
    for index, part in enumerate(hex_payload):
        print index, part, ''.join(format(ord(x), 'b') for x in part)
        payload += ''.join(format(ord(x), 'b').zfill(8) for x in part)
    dt = payload[:32]
    datasets = payload[32:]

    # calculate initial datetime
    seconds = int(dt[24:] + dt[16:24] + dt[8:16] + dt[:8], 2)
    data = [{}]

    for i in range(0, len(datasets) / 57):
        sub_data = [{}]
        dataset = datasets[:64]
        print('d: {0}'.format(dataset))
        datasets = datasets[64:]

        dataset_datetime = EPOCH_DATE + timedelta(seconds=seconds)
        seconds += 60
        satellite_datetime = datetime.strftime(dataset_datetime, '%Y%m%dT%H%M%SZ')

        # mode
        status = dataset[:8]

        # battery voltage

        u = float(int(dataset[8:16], 2))
        bat_v = round((u + 60) / 20, 2)

        # battery current
        u = float(int(dataset[16:24], 2))
        bat_c = round((u - 127) / 127, 2)

        # 3v3 current
        u = float(int(dataset[24:32], 2))
        v3_c = round(u / 40, 2)

        # 5v current
        u = float(int(dataset[32:40], 2))
        v5_c = round(u / 40, 2)

        # temperature comms
        u = float(int(dataset[40:48], 2))
        comms_t = round((u - 60) / 4, 2)

        # temperature eps
        u = float(int(dataset[48:56], 2))
        eps_t = round((u - 60) / 4, 2)

        # temperature battery
        u = float(int(dataset[56:], 2))
        batt_t = round((u - 60) / 4, 2)

        sub_data[0]['Sat Time'] = satellite_datetime
        sub_data[0]['Status'] = status
        sub_data[0]['VBAT'] = bat_v
        sub_data[0]['IBAT'] = bat_c
        sub_data[0]['I3V3'] = v3_c
        sub_data[0]['I5V0'] = v5_c
        sub_data[0]['TCOMMS'] = comms_t
        sub_data[0]['TEPS'] = eps_t
        sub_data[0]['TBAT'] = batt_t

        data[0][i] = sub_data

    response = {}
    response['type'] = 'WOD'
    response['content'] = data

    return response
