import os

from app.file_manager.file_manager import FileManager
from app.utils.decorators import user_authenticated
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings


@user_authenticated
def create(request):
    file_manager = FileManager(request.user)

    data = request.data

    try:
        file_manager.create(data.get("path"), data.get("name"), data.get("type"))
        return JsonResponse({"data": "created"}, status=201)
    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)


@user_authenticated
def get_directory(request):
    file_manager = FileManager(request.user)

    data = request.data
    try:
        if data.get("parent_dir"):
            files = file_manager.get_parent_directory_content(data.get("current_path"))
        else:
            files = file_manager.get_directory_content(data.get("current_path"))
        return JsonResponse(files)
    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)


@user_authenticated
def rename(request):
    file_manager = FileManager(request.user)

    data = request.data

    try:
        file_manager.rename(data.get("path"), data.get("name"))
        return JsonResponse({"data": "success"})
    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)


@user_authenticated
def delete(request):
    file_manager = FileManager(request.user)

    try:
        file_manager.delete(request.data.get("path"))
        return HttpResponse(status=204)
    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)


@require_GET
@user_authenticated
def download(request):
    file_manager = FileManager(request.user)
    try:
        rel_path = request.GET.get("path")

        if not rel_path:
            return JsonResponse({"data": "File path is required."}, status=400)

        abs_path = file_manager.resolve_path(rel_path)

        file_manager.check_access_permission(abs_path)

        file_manager.assert_exists(abs_path)

        return FileResponse(
            open(abs_path, "rb"),
            as_attachment=True,
            filename=os.path.basename(abs_path),
        )
    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)


@user_authenticated
def upload(request):
    file_manager = FileManager(request.user)
    upload_file = request.FILES.get("file")
    rel_path = request.POST.get("path", "")
    offset = int(request.POST.get("offset", 0))
    total_size = int(request.POST.get("total_size", 0))

    TMP_SUFFIX = '.incomplete'

    if not upload_file:
        return JsonResponse({"data": "No file provided."}, status=400)

    if total_size > settings.MAX_UPLOAD_SIZE:
        return JsonResponse(
            {
                "data": f"File size exceeds {int(settings.MAX_UPLOAD_SIZE / (1024 **2))}MB limit."
            },
            status=400,
        )
    try:

        normalized_path = (
            "." if rel_path == "/" else os.path.normpath(rel_path.lstrip("/"))
        )
        abs_path = os.path.abspath(file_manager.resolve_path(normalized_path))

        file_name = upload_file.name + TMP_SUFFIX

        new_file_path = os.path.join(abs_path, file_name)

        file_manager.check_access_permission(new_file_path)

        mode = "wb+" if offset == 0 else "rb+"

        with open(new_file_path, mode) as f:
            f.seek(offset)
            for chunk in upload_file.chunks():
                f.write(chunk)
            current_pos = f.tell()
            progress = int(current_pos / total_size * 100)
            is_complete = current_pos >= total_size
            if is_complete:
                os.rename(new_file_path, new_file_path.removesuffix(TMP_SUFFIX))

            return JsonResponse({
                "status": "complete" if is_complete else "in_progress",
                "progress": progress,
                "data": "Success" if is_complete else "Chunk received"
            }, status=201)

    except Exception as exc:
        return JsonResponse({"data": str(exc)}, status=400)
