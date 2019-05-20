import requests
base_folder = 'http://608dev.net/sandbox/sc/kms20/mafia/'
NEW = base_folder + "newGame.py"
VOTING = base_folder + "voting.py?kerberos="
GAMEDB = base_folder  + "gameDB.py"
UPDATE_URL = base_folder + 'updateGame.py'
KILLID_URL = base_folder + 'killerID.py'

#
#players = ['test1','test2','test3','test4','test5','test6','test7','test8','test9','test10','kms20']
#for player in players:
#    print(requests.post(NEW,data={'kerberos':player,'start':'False'}).text)
###
#print(requests.post(NEW,data={'kerberos':'kms20','start':'True'}).text)

#print(requests.get(base_folder + 'most_recent_game.py?kerberos=ellenwan',data={'kerberos':'ellenwan'}).text)
#print(requests.get(base_folder + 'killerID.py?kerberos=ellenwan&gameID=4',data={'kerberos':'ellenwan','gameID':'4'}).text)


print(requests.post(UPDATE_URL,data={'action':'','command':'day_end','gameID':'3'}).text)

#for player in players:
#    print(requests.post(NEW,data={'kerberos':player,'start':'False'}).text)
#
#print(requests.post(NEW,data={'kerberos':'kms20','start':'True'}).text)



#print(requests.get(KILLID_URL+'?kerberos=test1&gameID=0').text)

#print(requests.post(UPDATE_URL,data={'action':'espkill','killerID':'00001','gameID':'0','victim':'kms20'}).text)

#print(requests.post(VOTING,data={'kerberos':'test5','gameID':'2','vote':'test2','end_voting':'False'}).text)
#print(requests.post(VOTING,data={'kerberos':'test1','gameID':'2','vote':'test2','end_voting':'False'}).text)
#print(requests.post(VOTING,data={'kerberos':'test4','gameID':'2','vote':'test6','end_voting':'False'}).text)

#print(requests.post(VOTING,data={'gameID':'2','end_voting':'True'}).text)

#print(requests.post(GAMEDB,data={'kerberos':'test1','win':'True'}).text)

#print(requests.post(GAMEDB,data={'kerberos':'kms20','win':'True'}).text)


#requests.post(UPDATE_URL,data={'setup':'setup'})


#requests.post(UPDATE_URL,data={'setup':'setup'})
