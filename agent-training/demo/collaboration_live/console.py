"""Readable classroom console presentation for the recorded graph events."""
import json

NAMES = {
    'Researcher': '资料员', 'Analyst': '分析员', 'Writer': '撰写员',
    'Critic': '审查员', 'Supervisor': '主管', 'CEO': '总负责人',
    'ResearchLead': '资料团队负责人', 'DeliveryLead': '交付团队负责人',
    'research_team': '资料团队', 'delivery_team': '交付团队',
    'Runtime': '运行器', 'END': '结束', 'ESCALATE': '上报总负责人',
    'sequential': '顺序链', 'supervisor': '主管调度',
    'hierarchical': '层次化', 'swarm': '角色交接', 'network': '对等网络',
}
FIELDS = {'meal': '餐费', 'meal_ref': '餐费引用', 'venues': '场馆资料',
          'weather': '天气', 'proposal': '出游建议', 'analysis': '费用核算'}
STATUS = {'completed': '已完成', 'needs_input': '需补充资料或修订方案',
          'no_solution': '无可行方案', 'failed': '运行失败',
          'stopped': '达到运行上限', 'cancelled': '已取消'}


def name(value):
    return NAMES.get(value, value)


def issues_text(issues):
    return '、'.join(FIELDS.get(item, item) for item in issues) or '无'


class ConsolePresenter:
    def __init__(self, show_state=False, step=False):
        self.show_state, self.step = show_state, step
        self.actor = None
        self.provider = None

    def show_model(self, metadata):
        identity = (metadata.get('provider'), metadata.get('model'))
        if identity != self.provider:
            print(f'模型：{identity[0]} / {identity[1]}', flush=True)
            self.provider = identity

    def __call__(self, event):
        kind, actor = event['kind'], event['actor']
        if kind == 'model_switch':
            print('模型切换：' + event['message'], flush=True)
            self.show_model(event['provider'])
            return
        if kind == 'model_request':
            if actor != self.actor:
                print(f'\n── {name(actor)} ──', flush=True)
                self.actor = actor
            if event.get('provider'):
                self.show_model(event['provider'])
            print('正在请求模型…', flush=True)
        elif kind == 'model_response':
            print('回复：' + event['message'], flush=True)
        elif kind == 'work':
            return  # The same summary was already shown in model_response.
        elif kind == 'tool_result':
            result = json.loads(event['message'])
            if result.get('issues'):
                summary = '缺少或待处理：' + issues_text(result['issues'])
            elif 'analysis' in result:
                summary = f"费用核算完成，共 {len(result['analysis'])} 个候选"
            else:
                summary = '资料已读取'
            print('工具结果：' + summary, flush=True)
        elif kind == 'graph_update':
            state = event['state']
            print(f"\n节点完成：{name(actor)}\n"
                  f"  费用核算：{'已完成' if state['analyzed'] else '未完成'}\n"
                  f"  方案验收：{'已通过' if state['approved'] else '未通过'}\n"
                  f"  待处理项：{issues_text(state['issues'])}", flush=True)
            if self.show_state:
                print(json.dumps(state, ensure_ascii=False, indent=2), flush=True)
            self.actor = None
            if self.step:
                input('\n按 Enter 继续下一节点…')
        elif kind == 'finish':
            print('\n运行结束：' + STATUS.get(event['message'], event['message']), flush=True)
        else:
            label = {'model_rejected': '行动未通过校验', 'dispatch': '任务分派',
                     'handoff': '角色交接', 'route': '下一节点',
                     'escalate': '问题上报'}.get(kind, '协作进度')
            route = f"{name(actor)} → {name(event['target'])}：" if actor != event['target'] else ''
            print(f'{label}：{route}{event["message"]}', flush=True)
