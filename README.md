
# Teleport directory server implementation

[Teleport Transactions](https://github.com/bitcoin-teleport/teleport-transactions/) is software aiming to improve the [privacy](https://en.bitcoin.it/wiki/Privacy) of [Bitcoin](https://en.bitcoin.it/wiki/Main_Page).

Teleport Transactions depends on federated directory servers, which are described in the design docuemnt: https://gist.github.com/chris-belcher/9144bd57a91c194e332fb5ca371d0964#creating-a-communication-network-using-federated-message-boards The concept is also discussed on a JoinMarket issue here: https://github.com/JoinMarket-Org/joinmarket-clientserver/issues/415

This github project is an implementation of these directory servers used in Teleport.

To run, simply run the python script: `python3 teleportdirectoryserver.py`

