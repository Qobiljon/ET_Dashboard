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
![alt text](https://github.com/Qobiljon/ET_Dashboard/blob/master/images/et-building-blocks.png)

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

The campaign management module provides such functionalities as campaign creation, editing, deletion, and the management of data sources associated with campaigns. This module serves our Web Dashboard, which does not play a role during Third-Party Application integration. The Web Dashboard makes a use of this module to serve campaigners.

* Campaign creation
   * This functionality creates campaign in the server database with the provided details about a campaign (i.e., title, data sources, data source configurations, campaign start and end times, etc.)
* Campaign editing
   * This functionality provides a service to Web Dashboard of modifying details / configurations of already existing campaign details (i.e., adding a data source, changing a sensor’s sampling rate, changing start and end times, etc.)
* Campaign deletion
   * Using this functionality, the Web Dashboard can delete an existing campaign. Note: a campaign can be deleted only from the profile of the campaign’s creator.
* Retrieving all data sources
   * This functionality provides the Web Dashboard all available data sources (i.e., available sensors, surveys, etc.)
* Data source binding / creaton
   * Using this functionality, the Web Dashboard can attach data sources to their campaign. In other words, campaign’s data sources (and their configurations, such as sampling rates) become available for the Third-Party applications. Also, the data source binding functionality will automatically create a new data source and attach it to the campaign if one has not been registered in the server’s database before.

### Data management module

This module is responsible for storing data (i.e., sensor readings, EMAs, etc.), calculating statistics (i.e., DQ:Completeness, LOF, etc.), and providing the data at a request (i.e., for viewing/downloading data on Web Dashboard).
* Data storage (i.e., sensor, EMA, etc.)
   * This functionality is for storing the data when a Third-Party application submits one.
* Retrieving / extracting data (for filtering / downloading)
* Data processing (DQ: completeness, LOF: unexpected abnormal behavior)
   * The data processing pipeline is an always running process that calculates DQ:Completeness, LOF, and other statistics (i.e., participation duration, etc.) for presenting them on the Web Dashboard.

### Communication management module

This module simply provides four functionalities, two of which are for sending/receiving direct messages, and the other two for sending/receiving notifications. The messages and notifications are stored on the server’s database, and it is up to the Third-Party application’s designer to decide how to present the messages and notifications within their applications.
* Storing message (for sending direct message)
   * By using this functionality stores a new direct message record that will be labeled as an ‘unread message’ for the destination user. 
* Retrieving unread messages (for receiving unread direct messages)
   * When this functionality is used, the calling user can retrieve the unread messages directly sent to him/her, if ones are available in the server database.
* Storing a notification
   * This functionality is for a Web Dashboard, that broadcasts a message to all participants that are bound (have joined) to a particular campaign.
* Retrieving an unread notification
   * This functionality is for Third-Party applications to retrieve all unread notifications targeted to their bound (joined) campaign.

### Data processing pipeline

Data processing pipeline is an always running process that calculates statistics related to each campaign, data source, and each participant.
* DQ:Completeness calculation
   * Completeness is calculated using a simple formula:
      * Real amount of samples / Expected amount of samples → (%)
* LOF Calculation (for abnormal behavior detection)
   * Using [LOF](https://dl.acm.org/doi/10.1145/342009.335388), and [LoOP](https://pypi.org/project/PyNomaly/) algorithms
* Other statistics
   * Participation duration
      * Difference between the current day and participant’s day of participation
   * Last sync time
      * The timestamp taken from the last sample that was submitted by a participant
   * Last heartbeat time
      * The last time a participant’s device was online (accessible)


## Third-Party App integration

Third-Party applications can make remote procedure calls to the EasyTrack gRPC server in order to do various actions (i.e., submit sensor data, send a direct message to a campaigner, retrieve EMA, etc.). We provided a library for Third-Party application developers to make the integration much easier, which are explained in detail in this section. Also, a sample app is available for testing via [this link.](https://github.com/Qobiljon/EasyTrack_AndroidAgent) Simply, the steps need to be taken to integrate a third-party app with EasyTrack platform are as follows :
   1. Use our assistant application to authenticate users
   2. Bind the authenticated user to your campaign
   3. Actions of data / communication management modules in any order, i.e.:
       1. Submitting data
       2. Retrieving unread notifications / direct messages
       3. Retrieving data
       4. etc.

### Authenticator assistant application







