class _PeerState():
    def __init__(self, am_choking: bool, am_interested: bool, peer_choking: bool, peer_interested: bool):
        self.am_choking = am_choking
        self.am_interested = am_interested
        self.peer_choking = peer_choking
        self.peer_interested = peer_interested


    def __eq__(self, peer_state: '_PeerState'): 
        if self.am_choking != peer_state.am_choking:
            return False
        if self.am_interested != peer_state.am_interested:
            return False
        if self.peer_choking != peer_state.peer_choking: 
            return False
        if self.peer_interested != peer_state.peer_interested:
            return False
        return True


    def  __ne__(self, peer):
        return not self.__eq__(peer)
    

    def __str__(self):
        return f"""(is choking: {str(self.am_choking)}
        is interested: {str(self.am_interested)}
        peer choking: {str(self.peer_choking)}
        peer interested: {str(self.peer_interested)})"""


#Inital base state
INITIAL = _PeerState(
    am_choking=True,
    am_interested=False,
    peer_choking=True,
    peer_interested=False
)

NULL = _PeerState(
    am_choking=False,
    am_interested=False,
    peer_choking=False,
    peer_interested=False
)

#Download states

#Base state where self not interested and peer not choking
D0 = _PeerState(
    am_choking=True,
    am_interested=False,
    peer_choking=True,
    peer_interested=False
)

#Self interested but peer choking
D1 = _PeerState(
    am_choking=True,
    am_interested=True,
    peer_choking=True,
    peer_interested=False
)

#Self interested and peer not choking
D2 = _PeerState(
    am_choking=True,
    am_interested=True,
    peer_choking=False,
    peer_interested=False
)

#Upload states

#Base state where self not interested and peer not choking
U0 = _PeerState(
    am_choking=True,
    am_interested=False,
    peer_choking=True,
    peer_interested=False
)

#self interested but peer choking
U1 = _PeerState(
    am_choking=True,
    am_interested=True,
    peer_choking=True,
    peer_interested=False
)

#self interested and peer not choking
U2 = _PeerState(
    am_choking=True,
    am_interested=True,
    peer_choking=False,
    peer_interested=False
)
