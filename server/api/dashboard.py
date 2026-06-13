"""仪表盘统计 API"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from database import get_db
from core.deps import get_current_user
from models import Project, UICase, APICase, APITestCase, TestRun

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取仪表盘统计数据"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=now.weekday())  # 本周一
    last_week_start = week_start - timedelta(days=7)

    # 项目总数
    project_count = db.query(func.count(Project.id)).scalar() or 0
    # 本周新增项目
    week_new_projects = db.query(func.count(Project.id)).filter(
        Project.created_at >= week_start
    ).scalar() or 0

    # UI 用例数
    ui_case_count = db.query(func.count(UICase.id)).scalar() or 0
    week_new_ui = db.query(func.count(UICase.id)).filter(
        UICase.created_at >= week_start
    ).scalar() or 0

    # 接口用例数（包括旧的 APICase 和新的 APITestCase）
    api_case_count = db.query(func.count(APICase.id)).scalar() or 0
    api_test_case_count = db.query(func.count(APITestCase.id)).scalar() or 0
    total_api_cases = api_case_count + api_test_case_count
    week_new_api = db.query(func.count(APICase.id)).filter(
        APICase.created_at >= week_start
    ).scalar() or 0
    week_new_api += db.query(func.count(APITestCase.id)).filter(
        APITestCase.created_at >= week_start
    ).scalar() or 0

    # 今日执行数
    today_run_count = db.query(func.count(TestRun.id)).filter(
        TestRun.created_at >= today_start
    ).scalar() or 0
    # 昨日执行数
    yesterday_run_count = db.query(func.count(TestRun.id)).filter(
        TestRun.created_at >= yesterday_start,
        TestRun.created_at < today_start
    ).scalar() or 0

    # 总执行数
    total_run_count = db.query(func.count(TestRun.id)).scalar() or 0

    # 最近一次执行
    last_run = db.query(TestRun).order_by(TestRun.created_at.desc()).first()
    last_run_info = None
    if last_run:
        last_run_info = {
            "id": last_run.id,
            "name": last_run.name,
            "status": last_run.status,
            "created_at": last_run.created_at.strftime("%Y-%m-%d %H:%M:%S") if last_run.created_at else None,
        }

    # 今日较昨日的变化百分比
    def calc_day_trend(today, yesterday):
        if yesterday == 0:
            return 100 if today > 0 else 0
        return round((today - yesterday) / yesterday * 100, 1)

    return {
        "project_count": project_count,
        "ui_case_count": ui_case_count,
        "api_case_count": total_api_cases,
        "today_run_count": today_run_count,
        "total_run_count": total_run_count,
        "last_run": last_run_info,
        "trends": {
            "project": week_new_projects,
            "ui_case": week_new_ui,
            "api_case": week_new_api,
            "today_run": calc_day_trend(today_run_count, yesterday_run_count),
        },
    }


@router.get("/recent-runs")
def get_recent_runs(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取最近执行记录"""
    runs = db.query(TestRun).order_by(
        TestRun.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": run.id,
            "name": run.name,
            "test_type": run.test_type,
            "status": run.status,
            "total_count": run.total_count or 0,
            "pass_count": run.pass_count or 0,
            "fail_count": run.fail_count or 0,
            "error_count": run.error_count or 0,
            "duration": run.duration,
            "created_at": run.created_at.strftime("%Y-%m-%d %H:%M:%S") if run.created_at else None,
        }
        for run in runs
    ]


@router.get("/run-trend")
def get_run_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取执行趋势（最近N天）"""
    # 使用本地时间查询（避免时区比较问题）
    today_local = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today_local - timedelta(days=days - 1)

    # 查询每天的执行统计
    runs = db.query(TestRun).filter(
        TestRun.created_at >= start_date
    ).all()

    # 按日期分组统计（使用本地时间）
    trend_data = {}
    for i in range(days):
        date = (today_local - timedelta(days=days - 1 - i)).strftime("%m-%d")
        trend_data[date] = {"date": date, "total": 0, "pass": 0, "fail": 0, "error": 0}

    for run in runs:
        if run.created_at:
            # 直接格式化日期，忽略时区
            date = run.created_at.strftime("%m-%d")

            if date in trend_data:
                trend_data[date]["total"] += 1
                # 统计通过/失败/错误数
                if run.pass_count:
                    trend_data[date]["pass"] += run.pass_count
                if run.fail_count:
                    trend_data[date]["fail"] += run.fail_count
                if run.error_count:
                    trend_data[date]["error"] += run.error_count
                # 如果没有详细统计，根据状态判断
                if not run.pass_count and not run.fail_count and not run.error_count:
                    if run.status == "done":
                        trend_data[date]["pass"] += run.total_count or 1
                    elif run.status == "error":
                        trend_data[date]["error"] += run.total_count or 1

    return list(trend_data.values())


@router.get("/pass-rate")
def get_pass_rate(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取测试通过率"""
    # 查询最近的执行记录（包括所有完成的记录）
    recent_runs = db.query(TestRun).filter(
        TestRun.status.in_(["done", "completed"])
    ).order_by(TestRun.created_at.desc()).limit(100).all()

    total_pass = 0
    total_fail = 0
    total_error = 0

    for run in recent_runs:
        if run.pass_count:
            total_pass += run.pass_count
        if run.fail_count:
            total_fail += run.fail_count
        if run.error_count:
            total_error += run.error_count
        # 如果没有详细统计，根据状态判断
        if not run.pass_count and not run.fail_count and not run.error_count:
            total_pass += run.total_count or 1

    total = total_pass + total_fail + total_error

    return {
        "total": total,
        "pass": total_pass,
        "fail": total_fail,
        "error": total_error,
        "pass_rate": round(total_pass / total * 100, 1) if total > 0 else 0,
    }


@router.get("/case-distribution")
def get_case_distribution(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取用例分布"""
    ui_case_count = db.query(func.count(UICase.id)).scalar() or 0
    api_case_count = db.query(func.count(APICase.id)).scalar() or 0
    api_test_case_count = db.query(func.count(APITestCase.id)).scalar() or 0

    return [
        {"name": "UI 用例", "value": ui_case_count},
        {"name": "接口用例", "value": api_case_count + api_test_case_count},
    ]
