def test_get_sam_project_info(sam_project):
    from aws_testlib.core.introspection import get_sam_project_info

    get_sam_project_info()
