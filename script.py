import json
import datetime
import os
import csv
import xml.etree.ElementTree as ET
import mandrill


class Email():
    """
    Class that sends email via mandrill.
    """
    def send_mail(self, subject, text, to):
        md = mandrill.Mandrill('MANDRILL_KEY')
        message = {
            'auto_html': True,
            'auto_text': False,
            'to': [{
                'email': to,
                'name': 'Recipient Name',
                'type': 'to'
            }],
            'from_email': 'no-reply@from.com',
            'from_name': 'From',
            'important': 'true',
            'track_click': 'true',
            'subject': subject,
            'text': text
        }

        result = md.messages.send(
            message=message, async=False, ip_pool='Main Pool'
        )
        print(result)


class XMLVerify:
    ''' Class that verifies the xml files'''

    def __init__(self):
        self.email = Email()
        self.to = ['to@gmail.com', 'to2@gmail.com']

    def get_current_date_time_str(self):
        # return current datetime in string
        return datetime.datetime.now().strftime("%m%d%Y%I%M%S(%p)")

    def main(self):
        new_files = []

        # ***** Step 1 starts ******

        # Opening xmlprocessing file
        try:
            json_data = open('xmlprocessing.json')
            data = json.load(json_data)

            # location of xml files
            xml_files_dir = data[0]['xml_files_dir']

            # list of emails
            store_emails = data[0]['store_emails']
            json_data.close()

            # ***** Step 2 starts ******

            # looking for new xml files
            for file in os.listdir(xml_files_dir):
                if file.endswith(".xml"):
                    new_files.append(file)

            # ***** Step 2 ends ******
        except:
            # Open a log file for writing
            current_datetime_str = self.get_current_date_time_str()
            error_message = ''.join(["Cannot open xmlprocessing_valid.json {datetime-", current_datetime_str, "}"])
            with open('xmlprocessing-error.csv', 'wb') as csvfile:
                logwriter = csv.writer(
                    csvfile, delimiter=' ',
                    quotechar='|', quoting=csv.QUOTE_MINIMAL
                )
                logwriter.writerow([error_message])
            for each_mail in self.to:
                self.email.send_mail(subject="Cannot open xmlprocessing_valid.json", text=error_message, to=each_mail)

        # ***** Step 1 ends ******

        # ***** Step 3 starts ******

        current_path = os.path.dirname(os.path.abspath(__file__))
        directory = ''.join([current_path, "/XMLVERIFICATION/"])
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_name = ''.join(["XML_Log_{datetime-", self.get_current_date_time_str(), "}.csv"])
        file_path = ''.join([directory, file_name])
        with open(file_path, 'wb') as errorfile:

            # ***** Step 3 ends ******

            # ***** Step 4 starts ******

            errorlog = csv.writer(
                errorfile, delimiter=' ',
                quotechar='|', quoting=csv.QUOTE_MINIMAL
            )
            error_message = ''.join(["Started ", self.get_current_date_time_str()])
            error_message = error_message + " - No new files" if len(new_files) == 0 else error_message
            errorlog.writerow([error_message])

            # ***** Step 4 ends ******

            # ***** Step 5 starts ******

            if len(new_files) != 0:
                product_list_data = open('product_list.txt')
                product_list_json = json.load(product_list_data)
                product_type_set = {x['typeid'] for x in product_list_json}
                product_size_set = {x['sizeid'] for x in product_list_json}
                print('Product Types: \n', product_type_set)
                print('\nProduct Size: \n', product_size_set)

                for each_file in new_files:
                    xml_errors = []
                    print(each_file)
                    errorlog.writerow(["Processing " + each_file])
                    try:
                        tree = ET.parse('xmlprocessing/' + each_file)
                        root = tree.getroot()
                    except:
                        errorlog.writerow(
                            [
                                "Error parsing ", each_file, " datetime - ",
                                self.get_current_date_time_str()
                            ]
                        )
                        continue
                    for lineitem in root.iter('lineitem'):
                        try:
                            if int(lineitem[0].text) in product_type_set:
                                if int(lineitem[1].text) in product_size_set:
                                    continue
                                else:
                                    xml_errors.append(
                                        'Error - Invalid Product Size: {' +
                                        str(lineitem[1].text) +
                                        '} for file {' + str(each_file) + '}'
                                    )
                            else:
                                xml_errors.append(
                                    'Error - Invalid Product Type: {' +
                                    str(lineitem[0].text) +
                                    '} for file {' + str(each_file) + '}'
                                )
                                if int(lineitem[1].text) in product_size_set:
                                    continue
                                else:
                                    xml_errors.append(
                                        'Error - Invalid Product Size: {' +
                                        str(lineitem[1].text) +
                                        '} for file {' + str(each_file) + '}'
                                    )
                        except:
                            pass

                    # if no errors
                    if len(xml_errors) == 0:
                        print('No errors in file: ', each_file)
                        continue
                    else:
                        print('xml_errors: ', len(xml_errors))
                        error_dir = ''.join([current_path, "/XMLVERIFICATION/ERRORS/"])
                        current_file_name = current_path + '/xmlprocessing/' + each_file
                        new_file_name = ''.join(
                            [
                                error_dir, each_file,
                                ' Error Processing datetime - ',
                                self.get_current_date_time_str(),
                                '.xml'
                            ]
                        )
                        if not os.path.exists(error_dir):
                            os.makedirs(error_dir)
                        os.rename(current_file_name, new_file_name)

                        file_short_name = each_file[:3]
                        for each in store_emails:
                            if each['store'] == file_short_name:
                                emails = [i.strip() for i in each['email'].split(',')]
                                print(emails)
                                subject = "Error processing POS XML File on " + self.get_current_date_time_str()
                                text = ''.join(
                                    [
                                        "There was an error processing the POS XML file ",
                                        each_file, " on ", self.get_current_date_time_str(),
                                        ". The file had the following errors: \n\n", str(xml_errors),
                                        ".\n\n\n The file has been rejected. Please correct the",
                                        "problem and submit a new file."
                                    ]
                                )
                                for each_mail in emails:
                                    self.email.send_mail(subject=subject, text=text, to=each_mail)
                                errorlog.writerow(
                                    [
                                        'Error Email sent to ', each['email'], " on ",
                                        self.get_current_date_time_str()
                                    ]
                                )
                errorlog.writerow(['Ended ' + self.get_current_date_time_str()])
                    # break


verify_obj = XMLVerify()
verify_obj.main()
