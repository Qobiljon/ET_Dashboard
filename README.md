# Easy Track Platform
### Kobiljon Toshnazarov

Table of contents
=================
<!--ts-->
   * [1. Brief platform overview](#Brief-platform-overview)
   
   * [2. ET gRPC Server functionalities](#ET-gRPC-Server-functionalities)
      * [2.1. User management module](#User-management-module)
      * [2.2. Campaign management module](#2.2.-Campaign-management-module)
      * [2.3. Data management module](#2.3.-Data-management-module)
      * [2.4. Communication management module](#2.4.-Communication-management-module)
      * [2.5. Data processing pipeline](#2.5.-Data-processing-pipeline)
   * [3. Third-Party App integration](#3.-Third-Party-App-integration)
      * [3.1. Authenticator assistant application](#3.1.-Authenticator-assistant-application)
      * [3.2. Local-DB management library](#3.2.-Local-DB-management-library)
      * [3.3. Data submission management library](#3.3.-Data-submission-management-library)
      * [3.4. Notification management library](#3.4.-Notification-management-library)
      * [3.5. Direct message management library](#3.5.-Direct-message-management-library)
      * [3.6. Useful tips (i.e., power consumption, etc.)](#3.6.-Useful-tips-(i.e.,-power-consumption,-etc.))
   * [4. ET Web Dashboard manual](#4.-ET-Web-Dashboard-manual)
     * [4.1. Authentication](#4.1.-Authentication)
     * [4.2. Campaign creation / deletion](#4.2.-Campaign-creation-/-deletion)
        * [4.2.1. Data source creation](#4.2.1.-Data-source-creation)
     * [4.3. Campaign editing](#4.3.-Campaign-editing)
     * [4.4. Campaign monitoring](#4.4.-Campaign-monitoring)
     * [4.5. Viewing / downloading data](#4.5.-Viewing-/-downloading-data)
<!--te-->

## Brief platform overview
![alt text](https://raw.githubusercontent.com/Qobiljon/ET_Dashboard/master/et-building-blocks.png)

<p align="center">
   * Fig 1. EasyTrack Platform Design *
</p>
 
EasyTrack is a data collection platform for researchers to collect sensing data from mobile / wearable devices and monitor data collection statistics (i.e., missing data, etc). EasyTrack platform consists of four parts, which are: gRPC Server, Web Dashboard, EasyTrack Library for Third-Party apps, and a Third-Party App itself.

EasyTrack gRPC Server is the core part of the platform. It is responsible for storing, and processing data coming from third-party applications, and for providing charts to the web dashboard for monitoring purposes. EasyTrack Web dashboard is a simple (django) web application that retrieves data from gRPC server and visualizes in a browser. The major functionalities of the EasyTrack Library for third-party apps are: Local DB management, Data submission management, Notifications management, and Direct message management. The library helps researchers easily integrate their Third-Party Applications with our platform.

The following sections will guide you through the details about the EasyTrack gRPC server’s functionalities, Third-Party App integration tutorial, and the EasyTrack dashboard manual.



