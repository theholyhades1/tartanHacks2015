from pprint import pprint
from pysnap import Snapchat
from ripText import TextDetector
from imageProcessor import ImageProcessor

import random
import time

class RoundStage:
    Entries = 0
    Judging = 1

class GameInstance:
    players = []

    processedSnaps = []

    gameRound = 0
    roundStage = RoundStage.Entries
    roundStart = 0
    roundDuration = 60 * 5  # i.e. five minutes
    numCycles = 1
    gameFinished = False


    def restart(self):

        print "Resetting variables"

        self.api = Snapchat()
        self.api.login('snapsvshumanity', 'ilovetosnap69')
        # self.imp = ImageProcessor()
        # self.detector = TextDetector()

        self.gameRound = 0

        self.winner = ""

        counter = 0
        while True:
            newJudge = random.randint(0, len(self.players) -1)
            if self.players[newJudge] != self.judge or counter > 10:
                break
            counter += 1

        for i, player in enumerate(self.players):
            player['organizer'] = True if i == newJudge else False
            player['confirmed'] = False
            player['judged'] = False

        GameInstance.processedSnaps = []

        self.roundStage = RoundStage.Entries
        self.roundStart = 0
        self.roundDuration = 60 * 5
        self.numCycles = 1
        self.gameFinished = False

        self.run()

    # Constructor
    def __init__(self, organizer, gamePlayers):
        self.api = Snapchat()
        self.api.login('snapsvshumanity', 'ilovetosnap69')
        self.imp = ImageProcessor()

        self.detector = TextDetector()

        gameround = 0;

        self.players.append({
                            'username' : organizer,
                            'organizer': True,
                            'confirmed': False,
                            'judged'   : False
                        })

        for p in gamePlayers.split():
            currentPlayer = {
                            'username' : p,
                            'organizer': False,
                            'confirmed': False,
                            'judged'   : False
                    }
            self.players.append(currentPlayer)

        self.winner = ""

    # Main logic loop
    def run(self):
        self.api.clear_feed()
        self.friendPlayers()
        while (not GameInstance.gameFinished):
            print "In game loop, round:", self.gameRound
            print "Stage: ", self.roundStage
            snaps = self.pollAndFetchSnaps()
            self.processSnaps(snaps)

            if self.gameRound == 0:
                self.checkForAccepts()
            elif self.gameRound > self.numCycles * len(self.players):
                self.sendWinnerAndClose()
            elif self.roundStage == RoundStage.Entries:
                print "Self Entries: ", self.entries
                if (time.time() - self.roundStart > self.roundDuration):
                    self.roundStage = RoundStage.Judging
                    self.winner = str(self.entries[-1]['id'])
                    self.proceedToJudging()
                if (len(self.entries) >= len(self.players) - 1):
                    self.roundStage = RoundStage.Judging
                    self.winner = str(self.entries[-1]['id'])
                    self.proceedToJudging()
            elif self.roundStage == RoundStage.Judging:
                time.sleep(15)
                print "Judging!"
                if snaps != None:
                    print "WE FOUND A WINNER!"
                    self.sendWinnerAndClose()
                    break
            # else:
            #     print "This shouldn't happen"
            time.sleep(30)

        print "Game is over, starting again!"
        time.sleep(10)
        self.restart()

    # For each snap in snaps, OCR/classify
    def processSnaps(self, snaps):
        print "Processing ..."
        if snaps != None:
            print len(snaps)
            for snap in snaps:
                print "Processing a snap ...",
                text = self.detector.getText(snap['id'])[0]
                print "Text: ", text
                if text == "##CONFIRM":
                    for p in self.players:
                        if p['username'] == snap['sender']:
                            p['confirmed'] = True
                            break
                elif "##" in text:
                    print "THE WINNER IS", text
                if text.replace("##", "").isdigit(): print text
                if text.replace("##", "").isdigit() and self.roundStage == RoundStage.Judging and not self.gameRound == 0:
                    if int(text) <= len(self.entries):
                        announceRoundWinner(self.entries[int(text)]['userid'])
                        if (self.gameRound == self.numCycles * len(self.players)):
                            self.sendWinnerAndClose()
                        self.startRound()
                    else:
                        print "errrrrorrrrrr"
                elif self.roundStage == RoundStage.Entries and not self.gameRound == 0:
                    #if (snap['userid'] in [x['userid'] for x in self.entries]):
                    self.entries.append(snap)



    # Sends a snap to everyone announcing the round winner
    def announceRoundWinner(self, winnerid):
        pass

    # Checks to see who won by finding max score (from player object)
    def sendWinnerAndClose(self):
        names = [x['username'] for x in self.players]
        self.sendSnap('snaps/' + self.winner + ".jpg", ','.join(names), 10)

    # Send snapchats to users inviting them to play
    def sendInvitationSnap(self, users):
        # invitation snap = some stuff
        print users
        self.sendSnap('static/snap-confirm.jpg', users, 10)

    # Creates prompt image for current round
    def createPrompt(self):
        return 'static/blackcard.jpg'

    # Sends question prompts to all players as well as judge
    def sendPromptMessages(self):
        print "Sending prompty messages"
        prompt = self.createPrompt()
        judgenotify = 'static/snap-judge.jpg'
        names = [x['username'] for x in self.players]
        self.sendSnap(judgenotify, self.judge['username'], 10)
        print "Sent to judge"
        self.sendSnap(prompt, ','.join(names), 10)
        print "Sent to users"

    # Check to see if all unconfirmed players have accepted
    # Starts game if true
    def checkForAccepts(self):
        print "Checking for accepts"
        unconfirmedPlayers = [x for x in self.players
                if x['confirmed'] == False]
        print "Unconfirmed Players:", unconfirmedPlayers
        if (len(unconfirmedPlayers) == 0):
            self.gameRound = 1

            for player in self.players:
                if player['organizer']:
                    player['winner'] = None
                    player['judged'] = True
                    self.judge = player

            self.startRound()

    # Enters judging mode, sends all choices to judge
    def proceedToJudging(self):
        recipient = self.judge['username']
        for i, entry in enumerate(self.entries):
            # self.imp.addNumber(str(entry['id']), i + 1)
            path = 'snaps/' + entry['id'] + '.jpg'
            time = entry['time']
            self.sendSnap(path, recipient, time)

    # Initializes the round
    def startRound(self):
        print "Starting Round"
        self.roundStage = RoundStage.Entries
        self.entries = []
        self.sendPromptMessages()
        self.roundStart = time.time()

    # gets all new snaps, and returns a list of them
    def pollAndFetchSnaps(self):
        if self.roundStage == RoundStage.Judging: pass
        playernames = [x['username'] for x in self.players]
        foundSnaps = None
        while True:
            try:
                foundSnaps = self.api.get_snaps()
                break
            except:
                self.api.login('snapsvshumanity', 'ilovetosnap69')

        snaps = [x for x in self.api.get_snaps()
                if x['status'] == 1 # Unopened
                and x['sender'] in playernames
                and x['media_type'] == 0
                and x not in GameInstance.processedSnaps  # Is a photo, not a video
                ]

        successfullyDownloaded = []

        if snaps != None:
            for snap in snaps:
                if self.fetchPhotoSnap(snap['id']):
                    successfullyDownloaded.append(snap)
                    self.api.mark_viewed(snap['id'], 1)

        return successfullyDownloaded

    # Sends friend requests and invitations to all players
    def friendPlayers(self):
        friendslist = [x['name'] for x in self.api.get_friends()]
        toadd = [x['username'] for x in self.players
                    if x['username'] not in friendslist]
        # print "toAdd", toadd
        for user in toadd:
            self.api.add_friend(user)

        self.sendInvitationSnap(','.join([x['username'] for x in self.players]));
        print "All players are friended!"

    # Prints a list of current players
    def printPlayers(self):
        for p in self.players:
            print p['username']

    # Prints a list of all snaps that are available to download
    def listSnaps(self):
        snaps = [x for x in s.get_snaps() if x['status'] == 1]
        pprint(snaps)

    # Downloads and saves the snap with id snapid
    def fetchPhotoSnap(self, snapid):
        name = "snaps/" + snapid + ".jpg"
        if self.roundStage == RoundStage.Entries:
            self.winner = snapid
        f = open(name, 'wb')
        blob = self.api.get_blob(snapid)
        if blob == None:
            f.close()
            return False
        else:
            f.write(blob)
        f.close()
        return True

    # Sends a snapchat stored at path to recipients
    # recipients should be comma separated (no space!) list of usernames
    def sendSnap(self, path, recipients, time=5):
        mediaid = self.api.upload(path)
        self.api.send(mediaid, recipients, time)
