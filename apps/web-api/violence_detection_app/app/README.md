# Road Safety MOnitering System
## Introduction

This research presents an intelligent, real-time road safety and public security system designed to overcome the limitations of reactive CCTV-based monitoring. Additionally, the system also integrates illegal behavior recognition, and driver behavior monitoring from mobile application into a centralized response framework. 
The system includes deep learning - based accident detection, hybrid violence and illegal behavior recognition prioritizing accurate incident detection, severity assessment, and alert generation. While a mobile based driving assistant promotes proactive safety awareness with illegal driver behavior recognition, and monitoring. A central coordination engine prioritizes relevant emergency services and responses, targeting traffic authorities, emergency responders, law enforcement agencies, and individual drivers, notifying them, supporting safer and more responsive urban road environments.

## Architecture Diagram
<img width="1207" height="1204" alt="image" src="https://github.com/user-attachments/assets/caee64e6-d765-485a-9937-91a46250e7c8" />

## Components: 
- **Accident / Road Violation Detection** – Detects events such as accidents or unusual illegal vehicle movements from video streams using deep learning.  
- **Violence Detection** – Identifies violent actions and violent objects and fuses the information to generate context-based alert messages to the central unit.  
- **Session-based Driver Monitoring** – Monitors driver behavior in real-time, analyzes unsafe actions, and provides personalized feedback and safety scores.  
- **Coordination Hub for Emergencies** – Emergency coordination system that detects accidents or fires, prioritizes and dispatches responders, and notifies nearby users promptly.  

## Repository Structure
RoadSafetyAI/
│
├── README.md
├── .github
├── data
├── docs
├── infra
├── ops
├── packages
│
├── apps/
│   ├── inference-service/  # Includes api for mobile application
│   ├── mobile/    # Includes individual component source code for mobile application
│   ├── web-api/   # Inlcudes individual component source code for web application
│   └── web-frontend/  # Inlcudes individual component source code for web application frontends
│
├── .gitinore
├── .README.md
├── LICENCE


    ├── driver_game_monitoring/
    └── emergency_coordination/
