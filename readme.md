# Indigo

## What is it?

Indigo is the name for the public release of the datanode services that form the foundation of Ledgable's DLT infrastructure.
This infrastructure comprises of indexers, a configuration cluster and a smart web-platform that assists in configuration in addition to remote data-nodes that may be deployed as needed.

## What is DLT?

Distributed Ledger Technology could be viewed as the foundation service platform of Blockchain. 
The P2P (peer to peer) protocol is not REALLY decentralised - It appears that way. Effectively you need a "tracker" (which we call an indexer), that assists you in finding content.
Datanodes contact the indexer to receive information updates and configuration changes. 

## Datanodes?

A datanode is a storage and communication engine that manages a number of chains. YES you heard that right - Ledgable's datanode infrastructure can handle MULTIPLE chains simultaneously.
Additionally, ontop of this engine sits an API webserver that enables custom applications to be built such that you can retreive and push data into the chains.

## Whats released?

The datanode software is released today as OpenSource under the GPLv3 license. This is done to present transparency and integrity to the marketplace. What you choose to build ontop of this is upto you.
Ledgable's web-application does not store any other data than configuration (and account) information. As a result, all the data and communication channels are outside of Ledgable's perview.
For security reasons, we are not releasing the web-application platform. It is my intention that over time, this service will move to a foundation model.

## Bugs, bugs, bunny & more

Ok - there are likely to be bugs as this platform was built 100% by myself and there may be oversights. Im hoping that the community will help resolve these and move the platform forward. If you feel upto the challenge, please give me a shout at info@ledgable.com.
The web-application services will remain under direct control of the core company and we will oversee some new updates (planned). 

## Further Reading etc

Check the WIKI (above) to read about installation etc. Alternatively visit the host service (https://www.ledgable.com)

## Thanks

Of course thanks for the community and everyone thats helped in reaching this point. Looking forward to the next steps,

Samuel
Sept. 21st 2018 

