"""
Tests for job management tools.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import make_mock_ctx
from uipath_mcp.client import UiPathError


class TestListJobs:

    async def test_returns_structured_response(
        self, pat_settings, sample_jobs_response
    ):
        """list_jobs should call GET Jobs and return structured JSON."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=sample_jobs_response)
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        # Call the tool directly (bypass MCP dispatch for unit test speed)
        # Find the tool function
        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "list_jobs":
                tool_fn = tool.fn
                break
        assert tool_fn is not None

        result_str = await tool_fn(ctx=ctx, top=50, skip=0, order_desc=True)
        result = json.loads(result_str)

        assert result["total_count"] == 2
        assert len(result["jobs"]) == 2
        assert result["jobs"][0]["id"] == 101
        assert result["jobs"][0]["state"] == "Successful"

    async def test_returns_error_json_on_api_failure(self, pat_settings):
        """list_jobs should return a JSON error string when the API fails."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=UiPathError("API unavailable", status_code=503)
        )
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "list_jobs":
                tool_fn = tool.fn
                break

        result_str = await tool_fn(ctx=ctx)
        result = json.loads(result_str)
        assert "error" in result
        assert "unavailable" in result["error"].lower()


class TestStartJob:

    async def test_looks_up_release_key_then_starts_job(
        self, pat_settings, sample_releases_response
    ):
        """start_job should: (1) GET Releases to find key, (2) POST Jobs/StartJobs."""
        start_response = {
            "value": [
                {
                    "Id": 999,
                    "Key": "new-job-key",
                    "ReleaseName": "MyProcess",
                    "State": "Pending",
                    "Source": "Manual",
                    "CreationTime": "2024-01-15T12:00:00Z",
                }
            ]
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=sample_releases_response)
        mock_client.post = AsyncMock(return_value=start_response)
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "start_job":
                tool_fn = tool.fn
                break

        result_str = await tool_fn(ctx=ctx, process_name="MyProcess")
        result = json.loads(result_str)

        assert "jobs" in result
        assert result["jobs"][0]["id"] == 999
        # Verify two API calls were made
        assert mock_client.get.call_count == 1   # releases lookup
        assert mock_client.post.call_count == 1  # start job

    async def test_returns_error_when_process_not_found(self, pat_settings):
        """start_job should return an error if the process name doesn't exist."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={"value": []})
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "start_job":
                tool_fn = tool.fn
                break

        result_str = await tool_fn(ctx=ctx, process_name="NonExistentProcess")
        result = json.loads(result_str)
        assert "error" in result
        assert "NonExistentProcess" in result["error"]


class TestGetJobLogs:

    async def test_fetches_logs_filtered_by_job_key_in_python(self, pat_settings):
        """
        get_job_logs should:
        1. GET Jobs filtered by Key guid to get process name + time window
        2. GET RobotLogs filtered by ProcessName + time window in OData
        3. Narrow results in Python by JobKey (removes non-matching logs)
        """
        job_key = "1e10e835-9eef-41e6-ae2c-b0fb89ba18e7"
        jobs_response = {
            "value": [{
                "Id": 999,
                "Key": job_key,
                "ReleaseName": "MyProcess",
                "StartTime": "2026-01-01T10:00:00Z",
                "EndTime": "2026-01-01T10:05:00Z",
                "State": "Successful",
                "Source": "Manual",
                "CreationTime": "2026-01-01T10:00:00Z",
            }]
        }
        logs_response = {
            "value": [
                {"Id": 1, "JobKey": job_key, "Level": "Info", "Message": "Job started", "TimeStamp": "2026-01-01T10:00:01Z"},
                {"Id": 2, "JobKey": "other-key-not-matching", "Level": "Info", "Message": "Other job log", "TimeStamp": "2026-01-01T10:00:02Z"},
            ]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[jobs_response, logs_response])
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "get_job_logs":
                tool_fn = tool.fn
                break
        assert tool_fn is not None

        result_str = await tool_fn(ctx=ctx, job_key=job_key)
        result = json.loads(result_str)

        # Python-side filter should have removed the non-matching log
        assert result["count"] == 1
        assert result["logs"][0]["JobKey"] == job_key
        assert result["logs"][0]["Message"] == "Job started"
        # Two API calls: Jobs lookup + RobotLogs
        assert mock_client.get.call_count == 2

    async def test_returns_empty_when_job_not_found(self, pat_settings):
        """
        get_job_logs should return empty logs (not error) when the job key
        doesn't match any job — it still queries RobotLogs but Python filter
        removes all entries since none match the job key.
        """
        job_key = "00000000-0000-0000-0000-000000000000"
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[
            {"value": []},  # Jobs lookup: no match
            {"value": [{"Id": 1, "JobKey": "some-other-key", "Level": "Info", "Message": "unrelated"}]},
        ])
        ctx = make_mock_ctx(mock_client, pat_settings)

        from uipath_mcp.tools.jobs import register
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for tool in mcp._tool_manager._tools.values():
            if tool.name == "get_job_logs":
                tool_fn = tool.fn
                break
        assert tool_fn is not None

        result_str = await tool_fn(ctx=ctx, job_key=job_key)
        result = json.loads(result_str)

        assert result["count"] == 0
        assert result["logs"] == []


class TestGetJobRecording:

    JOB_KEY = "3ad083a6-0c2c-451b-be39-bcb8828cbb5d"
    WEBM = bytes.fromhex("1a45dfa3") + bytes(32)

    def _tool(self):
        from mcp.server.fastmcp import FastMCP
        from uipath_mcp.tools.jobs import register
        mcp = FastMCP("test")
        register(mcp)
        return next(t.fn for t in mcp._tool_manager._tools.values()
                    if t.name == "get_job_recording")

    def _job(self, folder=1333964, has_video=True):
        return {
            "Key": self.JOB_KEY, "ReleaseName": "DealerTrackDailyDrop_RE",
            "State": "Faulted", "OrganizationUnitId": folder,
            "OrganizationUnitFullyQualifiedName": "Revenue Management/DealertrackDailyDrop",
            "HasVideoRecorded": has_video,
        }

    @staticmethod
    def _resp(content_type, content=b"", json_body=None):
        import httpx
        if json_body is not None:
            return httpx.Response(200, json=json_body)
        return httpx.Response(200, content=content, headers={"content-type": content_type})

    def _descriptors(self, video_name="recording.webm", headers=None):
        base = f"https://blob.example/jobs/job-{self.JOB_KEY}/video/"
        return [
            {"uri": f"{base}{n}?sig=SECRET", "verb": "GET", "requiresAuth": False,
             "headers": headers or {"keys": None, "values": None}}
            for n in ("metadata.json", video_name, "thumbnail.png")
        ]

    async def test_searches_folders_and_uses_jobs_own_folder(self, pat_settings, tmp_path):
        """Without folder_id it finds the job's folder and fetches the recording there."""
        client = AsyncMock()
        client.collect_all = AsyncMock(return_value=[{"Id": 1332928}, {"Id": 1333964}])

        async def get_action(entity, action, params=None, folder_id=None):
            assert action == f"GetByKey(identifier={self.JOB_KEY})"
            if folder_id == 1333964:
                return self._job()
            raise UiPathError("not found", status_code=404)

        client.get_action = AsyncMock(side_effect=get_action)
        client.api_get_raw = AsyncMock(return_value=self._resp(None, json_body=self._descriptors()))
        client.download = AsyncMock(return_value=self._resp("application/octet-stream", self.WEBM))

        out = await self._tool()(
            ctx=make_mock_ctx(client, pat_settings), job_key=self.JOB_KEY,
            output_dir=str(tmp_path))
        result = json.loads(out)

        client.api_get_raw.assert_awaited_once_with(
            f"api/VideoRecording/jobs/{self.JOB_KEY}/read", folder_id=1333964)
        url = client.download.await_args.args[0]
        assert "/recording.webm?" in url
        assert "SECRET" not in out
        assert result["folder_id"] == 1333964
        assert (tmp_path / f"{self.JOB_KEY}.webm").read_bytes() == self.WEBM

    async def test_passes_descriptor_headers_and_auth(self, pat_settings, tmp_path):
        client = AsyncMock()
        client.get_action = AsyncMock(return_value=self._job())
        desc = self._descriptors(headers={"keys": ["x-ms-version"], "values": ["2023-01-03"]})
        desc[1]["requiresAuth"] = True
        client.api_get_raw = AsyncMock(return_value=self._resp(None, json_body=desc))
        client.download = AsyncMock(return_value=self._resp("video/webm", self.WEBM))

        await self._tool()(ctx=make_mock_ctx(client, pat_settings), job_key=self.JOB_KEY,
                           folder_id=1333964, output_dir=str(tmp_path))

        assert client.download.await_args.kwargs == {
            "headers": {"x-ms-version": "2023-01-03"}, "with_auth": True}

    async def test_reports_missing_recording_file(self, pat_settings, tmp_path):
        client = AsyncMock()
        client.get_action = AsyncMock(return_value=self._job())
        client.api_get_raw = AsyncMock(return_value=self._resp(
            None, json_body=self._descriptors()[:1]))
        result = json.loads(await self._tool()(
            ctx=make_mock_ctx(client, pat_settings), job_key=self.JOB_KEY,
            folder_id=1333964, output_dir=str(tmp_path)))
        assert result["files"] == ["metadata.json"]
        client.download.assert_not_called()

    async def test_surfaces_unexpected_lookup_errors(self, pat_settings):
        """A 400 (e.g. bad query) must not be reported as 'job not found'."""
        client = AsyncMock()
        client.get_action = AsyncMock(side_effect=UiPathError("bad request", status_code=400))
        result = json.loads(await self._tool()(
            ctx=make_mock_ctx(client, pat_settings), job_key=self.JOB_KEY, folder_id=1))
        assert result["status_code"] == 400

    async def test_reports_job_without_recording(self, pat_settings, tmp_path):
        client = AsyncMock()
        client.get_action = AsyncMock(return_value=self._job(has_video=False))
        result = json.loads(await self._tool()(
            ctx=make_mock_ctx(client, pat_settings), job_key=self.JOB_KEY,
            folder_id=1333964, output_dir=str(tmp_path)))
        assert "no video recording" in result["error"]
        client.api_get_raw.assert_not_called()

    async def test_rejects_non_guid_key(self, pat_settings):
        client = AsyncMock()
        result = json.loads(await self._tool()(
            ctx=make_mock_ctx(client, pat_settings), job_key="1 or 1 eq 1"))
        assert "not a valid" in result["error"]
        client.get_action.assert_not_called()
