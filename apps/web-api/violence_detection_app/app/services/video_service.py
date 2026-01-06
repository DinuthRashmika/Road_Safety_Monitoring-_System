import time
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.app.api.schemas.video_schema import (CameraListResponse, CameraResponse, SourceRequest, SourcePropertiesResponse)
from violence_detection_app.app.api.schemas.lrcn_schema import LrcnDetectionStartedResponse

class VideoService:

    def __init__(self):
        self.handler = VideoHandler()
        self.cameras = [
            {
                "id": "camera_01",
                "name": "Front Gate Camera",
                "source_type": "rtsp",
                "url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov",
                "location": "Front Gate",
                "status": "ONLINE"
            },
            {
                "id": "camera_02",
                "name": "Parking Area Camera",
                "source_type": "webcam",
                "url": "0",
                "location": "Parking Area",
                "status": "ONLINE"
            },
            {
                "id": "camera_03",
                "name": "Office Entrance Camera",
                "source_type": "file",
                "url": "videos/office.mp4",
                "location": "Office Entrance",
                "status": "OFFLINE"
            }
        ]


    def get_source_properties(self, request: SourceRequest) -> SourcePropertiesResponse:
        # If source_type is webcam, we can write those logic here
        # Eventhough we are not giving the relevent output from src, we can change SourcePropertiesResponse here and change what to show
        video_props = self.handler.get_video_properties(request.source_path)
        return SourcePropertiesResponse(

            fps=video_props["fps"],
            width=video_props["width"],
            height=video_props["height"],
            total_frames=video_props["frame_count"],
            duration=video_props["duration"],
            bitrate=video_props["bitrate"],
    )

    def start_processing(self, request: SourceRequest) -> LrcnDetectionStartedResponse:

        return LrcnDetectionStartedResponse (
            websocket_url="",
            success=True
        )
    
    def get_all_cameras(self) -> CameraListResponse:
        return CameraListResponse(
            count=len(self.cameras),
            cameras=[CameraResponse(**cam) for cam in self.cameras]
        )
