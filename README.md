# Internal-API-Server
This repo contains the source code of the AsyncAPY framework, which will be used to deploy an asynchronous TCP based API server with JSON requests meant for internal use at Intellivoid

# Documentation

AsyncAPY is divided into two things:


    - The AsyncAPY **protocol** which is the implementation of a TLV standard application protocol which handles incoming packets and stuff like that
    - The AsyncApy **framework**, basically a wrapper around the AsyncAPY protocol and a customizable base class


This documentation will face both components of the AsyncAPY library


## AsyncAPY - The Protocol

AsyncAPY's protocol is built on top of raw TCP, and now you might be wondering: "Why not HTTP?".
												                 
I know this looks like a NIH sindrome, but when I was building this framework I realized that HTTP was way too overkill for this purpose
and thought that creating a, simpler, dedicated application protocol to handle simple requests, would have done the thing. And it actually did!
(Moreover, HTTP is basically TCP with lots of headers so meh)

