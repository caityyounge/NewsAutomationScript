from bs4 import BeautifulSoup
import requests
import redis
from secrets import password, email_from, email_to


class Scraper:
    def __init__(self, keywords):
        self.markup = requests.get('https://news.ycombinator.com/').text
        self.keywords = keywords
        self.saved_links = ''
        self.r = redis.Redis(host='localhost', port=6379, db=0)

    def parse(self):
        soup = BeautifulSoup(self.markup, 'html.parser')
        links = soup.find_all(class_="storylink")
        self.saved_links = []
        for link in links:
            for keyword in self.keywords:
                if keyword in link.text:
                    self.saved_links.append(link)

    def store(self):
        self.saved_links = self.saved_links
        for link in self.saved_links:
            self.r.set(link.text, str(link))

    def email(self):
        links = [self.r.get(k) for k in self.r.keys()]
        links = str(links).splitlines()

        # Email Libraries
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Construct email
        from_email = email_from
        to_email = email_to

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Link"
        msg["From"] = from_email
        msg["To"] = to_email

        html = """
        <h4> %s link(s) you might find interesting today:</h4>

            %s

        """ % (len(links), '<br/><br/>'.join(links))

        mime = MIMEText(html, 'html')

        msg.attach(mime)

        # Send the message via local SMTP server.
        try:
            mail = smtplib.SMTP('smtp.gmail.com', 587)
            mail.ehlo()
            mail.starttls()
            mail.login(from_email, password)
            mail.sendmail(from_email, to_email, msg.as_string())
            mail.quit()
            print('Email sent!')
        except Exception as e:
            print('Something went wrong... %s' % e)

        # Refresh database
        self.r.flushdb()


s = Scraper(['python', 'crypto', 'startup', 'software engineer', 'new'])
s.parse()
s.store()

if __name__ == "__main__":
    s.email()
