import time
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.app.api.schemas.video_schema import (SourceRequest, SourcePropertiesResponse)
from violence_detection_app.app.api.schemas.lrcn_schema import LrcnDetectionStartedResponse

class VideoService:

    def __init__(self):
        self.handler = VideoHandler()

    def get_source_properties(self, request: SourceRequest) -> SourcePropertiesResponse:

        # If source_type is webcam, we can write those logic here
        """Eventhough we are not giving the relevent output from src, 
        we can change SourcePropertiesResponse here and change what to show"""
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
