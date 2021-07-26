# Easy Track Platform
### Kobiljon Toshnazarov

Table of contents
=================
<!--ts-->
   * [1. Brief platform overview](#Brief-platform-overview)
   
   * [2. ET gRPC Server functionalities](#ET-gRPC-Server-functionalities)
      * [2.1. User management module](#User-management-module)
      * [2.2. Campaign management module](#Campaign-management-module)
      * [2.3. Data management module](#Data-management-module)
      * [2.4. Communication management module](#Communication-management-module)
      * [2.5. Data processing pipeline](#Data-processing-pipeline)
   * [3. Third-Party App integration](#Third-Party-App-integration)
      * [3.1. Authenticator assistant application](#Authenticator-assistant-application)
      * [3.2. Local-DB management library](#Local-DB-management-library)
      * [3.3. Data submission management library](#Data-submission-management-library)
      * [3.4. Notification management library](#Notification-management-library)
      * [3.5. Direct message management library](#Direct-message-management-library)
      * [3.6. Useful tips (i.e., power consumption, etc.)](#Useful-tips-(i.e.,-power-consumption,-etc.))
   * [4. ET Web Dashboard manual](#ET-Web-Dashboard-manual)
     * [4.1. Authentication](#Authentication)
     * [4.2. Campaign creation / deletion](#Campaign-creation-/-deletion)
        * [4.2.1. Data source creation](#Data-source-creation)
     * [4.3. Campaign editing](#Campaign-editing)
     * [4.4. Campaign monitoring](#Campaign-monitoring)
     * [4.5. Viewing / downloading data](#Viewing-/-downloading-data)
<!--te-->

## Brief platform overview
![alt text](https://raw.githubusercontent.com/Qobiljon/ET_Dashboard/master/et-building-blocks.png)

<p align="center">
    Fig 1. EasyTrack Platform Design 
</p>
 
EasyTrack is a data collection platform for researchers to collect sensing data from mobile / wearable devices and monitor data collection statistics (i.e., missing data, etc). EasyTrack platform consists of four parts, which are: gRPC Server, Web Dashboard, EasyTrack Library for Third-Party apps, and a Third-Party App itself.

EasyTrack gRPC Server is the core part of the platform. It is responsible for storing, and processing data coming from third-party applications, and for providing charts to the web dashboard for monitoring purposes. EasyTrack Web dashboard is a simple (django) web application that retrieves data from gRPC server and visualizes in a browser. The major functionalities of the EasyTrack Library for third-party apps are: Local DB management, Data submission management, Notifications management, and Direct message management. The library helps researchers easily integrate their Third-Party Applications with our platform.

The following sections will guide you through the details about the EasyTrack gRPC server’s functionalities, Third-Party App integration tutorial, and the EasyTrack dashboard manual.

## ET gRPC Server functionalities

EasyTrack server’s RPCs are written in Google’s protobuf format. You can download and play with the RPCs by downloading the protobuf file from [our GitHub repository.](https://github.com/Qobiljon/EasyTrack_proto) The RPCs are served to both Third-Party Applications and [our Web Dashboard.](http://etdb.myvnc.com/) The RPCs are divided into separate modules, and to better understand them, the following subsections explain their functionalities in detail.

### User management module

The user management module provides registration, authentication, and campaign joining functionalities to campaign’s participants that use Third-Party Applications. Also, it separately provides registration, and authentication functionalities to campaign managers (campaigners) that use Web Dashboard.

* Authenticate using Google oAuth2 (third-party apps)
   * This functionality is for third-party applications, that is used for authenticating users with a Google oAuth2 ID token. Registration and authentication functionalities are merged into a single “Authenticate” functionality, as it automatically registers a user if it doesn’t exist in the system. As our assistant EasyTrack Authenticator application handles this functionality, one will not be required to work with this part while integrating a third-party application with EasyTrack platform.
* Google oAuth2 (dashboard)
   * This functionality works in the same way as above, serving the Web Dashboard instead of Third-Party Applications.
* Bind user to campaign
   * By using this functionality, users of Third-Party applications can join a campaign, where the server maps the participant with the specified campaign.

### Campaign management module



