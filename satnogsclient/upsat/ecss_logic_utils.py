import datetime
import logging
import time
import json

from satnogsclient.upsat import packet_settings


logger = logging.getLogger('satnogsclient')
log_path = ""


def ecss_logic(ecss_dict):

    global log_path

    id = 0
    text = "Nothing found"

    if ecss_dict['ser_type'] == packet_settings.TC_VERIFICATION_SERVICE:

        # We should have a list of packets with ack in order to return it
        report = "Wrong sub type"
        if ecss_dict['ser_subtype'] == packet_settings.TM_VR_ACCEPTANCE_SUCCESS:
            report = "OK"
        elif ecss_dict['ser_subtype'] == packet_settings.TM_VR_ACCEPTANCE_FAILURE:
            report = "Error " + packet_settings.SAT_RETURN_STATES[ecss_dict['data'][4]]

        text = "ACK {0}".format(report)

    elif ecss_dict['ser_type'] == packet_settings.TC_HOUSEKEEPING_SERVICE and ecss_dict['ser_subtype'] == packet_settings.TM_HK_PARAMETERS_REPORT:

        struct_id = ecss_dict['data'][0]

        if ecss_dict['app_id'] == packet_settings.EPS_APP_ID and struct_id == packet_settings.HEALTH_REP:

            report = "VBAT:" + str(ecss_dict['data'][1] * 0.0716) + "V "
            report += "IBAT:" + str(ecss_dict['data'][2] * 4.6 + 1000) + "mA "
            report += "3V3:" + str(ecss_dict['data'][3] * 11.72) + "mA "
            report += "5V0:" + str(ecss_dict['data'][4] * 11.72) + "mA "
            report += "TCPU:" + str((ecss_dict['data'][5] / 4) - 15) + "C "
            report += "TBAT:" + str((ecss_dict['data'][6] / 4) - 15) + "C"

        elif ecss_dict['app_id'] == packet_settings.EPS_APP_ID and struct_id == packet_settings.EPS_FLS_REP:

            pointer = 1
            report = "Safety Limit memory values:"

            report += "1: " + str(cnv8_32(ecss_dict['data'][pointer:])) + ", "
            pointer += 4
            report += "2: " + str(cnv8_32(ecss_dict['data'][pointer:])) + ", "
            pointer += 4
            report += "3: " + str(cnv8_32(ecss_dict['data'][pointer:])) + ", "
            pointer += 4
            report += "4: " + str(cnv8_32(ecss_dict['data'][pointer:])) + ", "
            pointer += 4
            report += "5: " + str(cnv8_32(ecss_dict['data'][pointer:]))

        elif ecss_dict['app_id'] == packet_settings.EPS_APP_ID and struct_id == packet_settings.EX_HEALTH_REP:

            pointer = 1
            report = eps_hk(ecss_dict['data'][pointer:])

        elif ecss_dict['app_id'] == packet_settings.COMMS_APP_ID and struct_id == packet_settings.HEALTH_REP:

            report = "data "

        elif ecss_dict['app_id'] == packet_settings.COMMS_APP_ID and struct_id == packet_settings.EX_HEALTH_REP:

            pointer = 1
            report = comms_hk(ecss_dict['data'][pointer:])

        elif ecss_dict['app_id'] == packet_settings.ADCS_APP_ID and struct_id == packet_settings.EX_HEALTH_REP:

            pointer = 1
            report = adcs_hk(ecss_dict['data'][pointer:])

        elif ecss_dict['app_id'] == packet_settings.ADCS_APP_ID and struct_id == packet_settings.SU_SCI_HDR_REP:

            pointer = 1
            report = "SU_SCI_HDR_REP "

            roll = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.01
            pointer += 2
            report += "roll " + str(roll) + " "

            pitch = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.01
            pointer += 2
            report += "pitch " + str(pitch) + " "

            yaw = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.01
            pointer += 2
            report += "yaw " + str(yaw) + " "

            roll_dot = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.001
            pointer += 2
            report += "roll_dot " + str(roll_dot) + " "

            pitch_dot = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.001
            pointer += 2
            report += "pitch_dot " + str(pitch_dot) + " "

            yaw_dot = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.001
            pointer += 2
            report += "yaw_dot " + str(yaw_dot) + " "

            x = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.5
            pointer += 2
            report += "x " + str(x) + " "

            y = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.5
            pointer += 2
            report += "y " + str(y) + " "

            z = cnv_signed_8_16(ecss_dict['data'][pointer:]) * 0.5
            pointer += 2
            report += "z " + str(z) + " "

        elif ecss_dict['app_id'] == packet_settings.OBC_APP_ID and struct_id == packet_settings.EX_HEALTH_REP:

            pointer = 1
            report = obc_hk(ecss_dict['data'][pointer:])

        elif struct_id == packet_settings.EXT_WOD_REP:
            content = [{}]

            pointer = packet_settings.OBC_EXT_WOD_OFFSET
            content[0]['OBC'] = obc_hk(ecss_dict['data'][pointer:])
            pointer = packet_settings.COMMS_EXT_WOD_OFFSET
            content[0]['COMMS'] = comms_hk(ecss_dict['data'][pointer:])
            pointer = packet_settings.ADCS_EXT_WOD_OFFSET
            content[0]['ADCS'] = adcs_hk(ecss_dict['data'][pointer:])
            pointer = packet_settings.EPS_EXT_WOD_OFFSET
            content[0]['EPS'] = eps_hk(ecss_dict['data'][pointer:])

            report_pre = [{
                "type": "EX_WOD",
                "content": content
            }]
            report = json.dumps(report_pre, indent=2, sort_keys=True)

        text = report

    elif ecss_dict['ser_type'] == packet_settings.TC_EVENT_SERVICE and ecss_dict['ser_subtype'] == packet_settings.TM_EV_NORMAL_REPORT:

        report = ""
        event_id = ecss_dict['data'][0]
        if event_id == packet_settings.EV_sys_boot:
            report = "booted"

        text += "EVENT {0}".format(report)

    elif ecss_dict['ser_type'] == packet_settings.TC_FUNCTION_MANAGEMENT_SERVICE:
        # Nothing to do here
        text += "FM {0}, FROM: {1}".format(packet_settings.upsat_app_ids[str(ecss_dict['app_id'])])

    elif ecss_dict['ser_type'] == packet_settings.TC_TIME_MANAGEMENT_SERVICE:

        # Check https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        if ecss_dict['ser_subtype'] == packet_settings.TM_TIME_REPORT_IN_UTC:

            wkd = ecss_dict['data'][0]
            day = ecss_dict['data'][1]
            mon = ecss_dict['data'][2]
            year = ecss_dict['data'][3]
            hour = ecss_dict['data'][4]
            mins = ecss_dict['data'][5]
            sec = ecss_dict['data'][6]

            report = str(year) + "-" + str(mon) + "-" + str(day) + " " + str(hour) + ":" + str(mins) + ":" + str(sec) + " wkd:" + str(wkd)

        elif ecss_dict['ser_subtype'] == packet_settings.TM_TIME_REPORT_IN_QB50:

            qb50 = cnv8_32(ecss_dict['data'][0:])
            utc = qb50_to_utc(qb50)
            report = "QB50 " + str(qb50) + " UTC: " + str(utc)

        text = "TIME: {0}".format(report)

    elif ecss_dict['ser_type'] == packet_settings.TC_SCHEDULING_SERVICE:
        text = "APO, DO LET US KNOW WHAT TO DO HERE"
    elif ecss_dict['ser_type'] == packet_settings.TC_LARGE_DATA_SERVICE:
        text = "FM {0}, FROM: {1}".format(ecss_dict['app_id'])
    elif ecss_dict['ser_type'] == packet_settings.TC_MASS_STORAGE_SERVICE:

        report = ""
        if ecss_dict['ser_subtype'] == packet_settings.TM_MS_CATALOGUE_REPORT:

            for i in range(0, 7):

                offset = (i * packet_settings.SCRIPT_REPORT_SU_OFFSET)
                valid = ecss_dict['data'][(offset)]
                size = cnv8_32(ecss_dict['data'][(1 + offset):])
                fatfs = cnv8_32_fd(ecss_dict['data'][(5 + offset):])
                time_modfied = fatfs_to_utc(fatfs)

                print "offset: " + str(offset) + " script " + packet_settings.upsat_store_ids[str(i + 1)] + " valid: " + str(valid) + " size: " + str(size) + \
                    " time_modified: " + str(time_modfied)
                print "raw ", ' '.join('{:02x}'.format(x) for x in ecss_dict['data'][(offset):(offset + packet_settings.SCRIPT_REPORT_SU_OFFSET)])

                report += "script " + packet_settings.upsat_store_ids[str(i + 1)] + " valid: " + str(valid) + " size: " + str(size) + " time_modified: " + str(time_modfied) + "\n"

            for i in range(0, 4):

                offset = (7 * packet_settings.SCRIPT_REPORT_SU_OFFSET) + (i * packet_settings.SCRIPT_REPORT_LOGS_OFFSET)

                fnum = cnv8_16(ecss_dict['data'][(offset):])

                fname_tail = cnv8_16(ecss_dict['data'][(2 + offset):])
                tail_size = cnv8_32(ecss_dict['data'][(4 + offset):])
                fatfs_tail = cnv8_32_fd(ecss_dict['data'][(8 + offset):])
                time_modfied_tail = fatfs_to_utc(fatfs_tail)

                fname_head = cnv8_16(ecss_dict['data'][(12 + offset):])
                head_size = cnv8_32(ecss_dict['data'][(14 + offset):])
                fatfs_head = cnv8_32_fd(ecss_dict['data'][(18 + offset):])
                time_modfied_head = fatfs_to_utc(fatfs_head)

                print "offset: " + str(offset) + " script " + packet_settings.upsat_store_ids[str(i + 8)] + " number of files: " + str(fnum) + " tail size: " + str(tail_size) + \
                    " tail time_modfied: " + str(time_modfied_tail) + " head size: " + str(head_size) + " head time_modfied: " + str(time_modfied_head)
                print "raw ", ' '.join('{:02x}'.format(x) for x in ecss_dict['data'][(offset):(offset + packet_settings.SCRIPT_REPORT_LOGS_OFFSET)])

                report += "script " + packet_settings.upsat_store_ids[str(i + 8)] + " number of files: " + str(fnum) + " tail name: " + str(fname_tail) + " tail size: " + \
                    str(tail_size) + " tail time_modfied: " + str(time_modfied_tail) + " head name: " + str(fname_head) + " head size: " + str(head_size) + \
                    " head time_modfied: " + str(time_modfied_head) + "\n"

        elif ecss_dict['ser_subtype'] == packet_settings.TM_MS_CATALOGUE_LIST:

            sid = ecss_dict['data'][0]
            f_iter = cnv8_16(ecss_dict['data'][1:])

            if sid == packet_settings.SU_LOG or \
               sid == packet_settings.WOD_LOG or \
               sid == packet_settings.EXT_WOD_LOG or \
               sid == packet_settings.EVENT_LOG or \
               sid == packet_settings.FOTOS:

                files = (ecss_dict['size'] - 3) / packet_settings.LOGS_LIST_SIZE

                print "data size is: ", ecss_dict['size'], " ", (ecss_dict['size'] - 3) / packet_settings.LOGS_LIST_SIZE, " ", files
                # If su_logs > MAX_DOWNLINK_SU_LOGS:
                # Error

                ecss_dict['files'] = [0] * files
                ecss_dict['files_sid'] = sid

                report = "received file list, for store " + str(sid) + " with " + str(files) + " files, next file iteration is: " + str(f_iter) + "\n"
                for i in range(0, files):
                    filename = cnv8_16(ecss_dict['data'][(3 + (i * packet_settings.LOGS_LIST_SIZE)):])
                    size = cnv8_32(ecss_dict['data'][(5 + (i * packet_settings.LOGS_LIST_SIZE)):])
                    fatfs = cnv8_32_fd(ecss_dict['data'][(9 + (i * packet_settings.LOGS_LIST_SIZE)):])
                    time_modfied = fatfs_to_utc(fatfs)

                    # Ecss_dict['files'][i]['filename'] = filename
                    # Ecss_dict['files'][i]['time_modfied'] = time_modfied
                    # Ecss_dict['files'][i]['size'] = size

                    report += " file " + str(i) + " filename " + str(filename) + " size " + str(size) + " modified " + str(time_modfied) + "\n"
                print report

            elif sid <= packet_settings.SU_SCRIPT_7:
                report = "received file list, for store " + str(sid) + " you should do a report"

        elif ecss_dict['ser_subtype'] == packet_settings.TM_MS_CONTENT:

            sid = ecss_dict['data'][0]
            fname = cnv8_16(ecss_dict['data'][1:])

            report = "From store: " + packet_settings.upsat_store_ids[str(sid)] + " file " + str(fname)  # + " content " + ecss_dict['data'] + \
            # " " + ' '.join('{:02x}'.format(x) for x in ecss_dict['data']) + "\n"

            if sid == packet_settings.SU_LOG:

                su_logs = 1  # (ecss_dict['size'] - 3) / packet_settings.SU_LOG_SIZE

                # If su_logs > MAX_DOWNLINK_SU_LOGS:
                # Error

                report += " received " + str(su_logs) + " su logs "
                for i in range(0, su_logs):
                    qb50 = cnv8_32(ecss_dict['data'][(3 + (i * packet_settings.SU_LOG_SIZE)):])
                    utc = qb50_to_utc(qb50)
                    report += "SU LOG, with QB50 " + str(qb50) + " UTC: " + str(utc)

            elif sid == packet_settings.WOD_LOG:

                wod_logs = 1  # (ecss_dict['size'] - 3) / packet_settings.SU_LOG_SIZE

                # If su_logs > MAX_DOWNLINK_SU_LOGS:
                # Error

                report += " received " + str(wod_logs) + " wod logs "
                for i in range(0, wod_logs):
                    qb50 = cnv8_32(ecss_dict['data'][(3 + (i * packet_settings.WOD_LOG_SIZE)):])
                    utc = qb50_to_utc(qb50)
                    report += "WOD LOG, with QB50 " + str(qb50) + " UTC: " + str(utc)

            elif sid <= packet_settings.SU_SCRIPT_7:

                sum1 = 0
                sum2 = 0
                size = (ecss_dict['size'] - 3)
                for i in range(3, size):
                    sum1 = (sum1 + ecss_dict['data'][i]) % 255
                    sum2 = (sum2 + sum1) % 255
                if ((sum2 << 8) | sum1) == 0:
                    report += " Checksum ok"
                else:
                    report += " Checksum error"

            timestr = time.strftime("%Y%m%d-%H%M%S")

            fwname = log_path + packet_settings.upsat_store_ids[str(sid)] + "/" + str(fname) + "_" + timestr + ".bin"
            myfile = open(fwname, 'w')
            myfile.write(ecss_dict['data'][3:])
            myfile.close()

        text = "MS {0}".format(report)

    elif ecss_dict['ser_type'] == packet_settings.TC_TEST_SERVICE:
        text = "TEST Service from {0}".format(packet_settings.upsat_app_ids[str(ecss_dict['app_id'])])
    elif ecss_dict['ser_type'] == packet_settings.TC_SU_MNLP_SERVICE:
        text = "APO, DO LET US KNOW WHAT TO DO HERE"

    res_dict = {}
    res_dict['id'] = id
    res_dict['log_message'] = text
    res_dict['files'] = []
    res_dict['from_id'] = ecss_dict['app_id']
    return res_dict


# Decoding extened health report from OBC
def obc_hk(ecss_data):
    content = [{}]
    pointer = 0

    content[0]['Time'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['QB50'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['RST source'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Boot Cnt'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['Boot Cnt COMMS'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Boot Cnt EPS'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Last Assertion F'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion L'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RTC VBAT'] = str(cnv8_16(ecss_data[pointer:]) * 0.001611328)  # 2 * ( raw * ( 3.3 / 2 ^ 12 ))
    pointer += 2
    content[0]['Task time UART'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['Task time HK'] = str(cnv8_16(ecss_data[pointer:]) * 0.001)
    pointer += 2
    content[0]['Task time IDLE'] = str(cnv8_16(ecss_data[pointer:]) * 0.001)
    pointer += 2
    content[0]['Task time SU'] = str(cnv8_16(ecss_data[pointer:]) * 0.001)
    pointer += 2
    content[0]['Task time SCH'] = str(cnv8_16(ecss_data[pointer:]) * 0.001)
    pointer += 2
    content[0]['MS Last Err'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['SD Enabled'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['MS Err line'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['IAC State'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['SU Init Func Run time'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['SU Last Active script'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['SU Script Sch Active'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['SU Service Sch Active'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['tt_perm_norm_exec_count'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['tt_perm_exec_on_span_count'] = str(cnv8_16(ecss_data[pointer:]))

    report = [{
        "source": "OBC",
        "content": content
    }]
    return json.dumps(report, indent=2, sort_keys=True)


# Decoding extened health report from EPS
def eps_hk(ecss_data):
    content = [{}]
    pointer = 0

    content[0]['Time'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['RST source'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion F'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion L'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Batt Temp Health Status'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Heater status'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['TOP Voltage'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['TOP Current'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['TOP Duty'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['BOTTOM Voltage'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['BOTTOM Current'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['BOTTOM Duty'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['LEFT Voltage'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['LEFT Current'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['LEFT Duty'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['RIGHT Voltage'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RIGHT Current'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RIGHT Duty'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['ConC1'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['ConC2'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Temp sensor PWR SW'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Soft error status'] = str(ecss_data[pointer])

    report = [{
        "source": "EPS",
        "content": content
    }]
    return json.dumps(report, indent=2, sort_keys=True)


# Decoding extened health report from COMMS
def comms_hk(ecss_data):
    content = [{}]
    pointer = 0

    content[0]['Time'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['RST source'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion F'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion L'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Flash read transmit'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['Beacon pattern'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['RX Failed'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RX CRC Failed'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['TX Failed'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['TX Frames'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RX Frames'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Last TX Error'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Last RX Error'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Invalid Dest Frames Cnt'] = str(cnv8_16(ecss_data[pointer:]))

    report = [{
        "source": "COMMS",
        "content": content
    }]
    return json.dumps(report, indent=2, sort_keys=True)


# Decoding extened health report from ADCS
def adcs_hk(ecss_data):
    content = [{}]
    pointer = 0

    content[0]['Time'] = str(cnv8_32(ecss_data[pointer:]) * 0.001)
    pointer += 4
    content[0]['QB50'] = str(cnv8_32(ecss_data[pointer:])) + " " + qb50_to_utc(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['RST source'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Boot Cnt'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['Last Assertion F'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Last Assertion L'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['TX error'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['Roll'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Pitch'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Yaw'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Roll Dot'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Pitch Dot'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Yaw Dot'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['ECI X'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['ECI Y'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['ECI Z'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['GPS Status'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['GPS Sats'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['GPS Week'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['GPS Time'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['Temp'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Gyr X'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Gyr Y'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Gyr Z'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['XM X'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['XM Y'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['XM Z'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['RM X'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['RM Y'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['RM Z'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['RM Z'] = str(cnv8_32(ecss_data[pointer:]))
    pointer += 4
    content[0]['Sun V 0'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Sun V 1'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Sun V 2'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Sun V 3'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Sun V 4'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Spin RPM'] = str(cnv8_16(ecss_data[pointer:]))
    pointer += 2
    content[0]['Mg Torq V Y'] = str(ecss_data[pointer])
    pointer += 1
    content[0]['MG Torq V Z'] = str(ecss_data[pointer])

    report = [{
        "source": "ADCS",
        "content": content
    }]
    return json.dumps(report, indent=2, sort_keys=True)


def fatfs_to_utc(fatfs):
    fatfs_date = str(int('{:032b}'.format(fatfs)[:7], 2) + 1980) + '-' +\
        str(int('{:032b}'.format(fatfs)[7:11], 2)) + '-' +\
        str(int('{:032b}'.format(fatfs)[11:16], 2)) + ' ' +\
        str(int('{:032b}'.format(fatfs)[16:21], 2)) + ':' +\
        str(int('{:032b}'.format(fatfs)[21:27], 2)) + ':' +\
        str(int('{:032b}'.format(fatfs)[27:], 2) * 2)
    return fatfs_date


def qb50_to_utc(qb50):
    utc = datetime.datetime.utcfromtimestamp(qb50 + 946684800).strftime("%A, %d. %B %Y %H:%M:%S")
    return utc


def cnv32_8(inc):

    ret = [0] * 4

    ret[0] = inc & 0x000000FF
    ret[1] = (inc >> 8) & 0x000000FF
    ret[2] = (inc >> 16) & 0x000000FF
    ret[3] = (inc >> 24) & 0x000000FF
    return ret


def cnv16_8(inc):

    ret = [0] * 2

    ret[0] = inc & 0x00FF
    ret[1] = (inc >> 8) & 0x00FF
    return ret


def cnv8_32(inc):
    return ((inc[3] << 24) | (inc[2] << 16) | (inc[1] << 8) | (inc[0]))


def cnv8_32_fd(inc):
    return ((inc[1] << 24) | (inc[0] << 16) | (inc[3] << 8) | (inc[2]))


def cnv8_16(inc):
    return ((inc[1] << 8) | (inc[0]))


def cnv_signed_8_32(inc):
    res = ((inc[3] << 24) | (inc[2] << 16) | (inc[1] << 8) | (inc[0]))
    if (res >> 31) == 1:
        res = (0xFFFFFFFF - res) * -1
    return res


def cnv_signed_8_16(inc):
    res = ((inc[1] << 8) | (inc[0]))
    if (res >> 15) == 1:
        res = (0xFFFF - res) * -1
    return res
