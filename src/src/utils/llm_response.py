from openai import OpenAI
import json
import argparse
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def generate_analysis_report(scores, categories):
    client = OpenAI(api_key="sk-ykopfgiasttgvkyjbqkyirpobwbdfwbwleuhrcaslscphvpl", 
                    base_url="https://api.siliconflow.cn/v1")

    # 构造结构化输入
    input_data = {
        "scores": scores,
        "error_types": categories,
        "request_type": "生成健身报告"
    }

    # 配置请求消息
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的健身数据分析助手。根据用户提供的动作评分和错误类型数据，生成结构化训练报告。报告需包含以下部分：\n"
                      "1. 总体表现总结（平均分、最佳/最差表现）\n"
                      "2. 错误类型分布分析，：四类错误动作：Case0：标准动作；Case1：手臂复原不足；Case2：手臂下放过直；Case3：手肘抬起。\n"
                      "3. 针对性改进建议\n"
                      "要求：使用自然语言描述，分点列出，语言简洁专业。四类错误动作以Case1为例，用“手臂复原不足”表示而不是“Case1”。回答使用markdown格式。"
        },
        {
            "role": "user",
            "content": json.dumps(input_data, ensure_ascii=False)
        }
    ]

    try:
        # 调用API
        response = client.chat.completions.create(
            model='deepseek-ai/DeepSeek-V3',
            messages=messages,
            temperature=0.3,  # 控制创造性，越低输出越确定
            stream=False  # 改为非流式输出
        )

        # 返回生成的建议
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating report: {str(e)}", file=sys.stderr)
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成运动分析报告')
    parser.add_argument('--scores', type=str, required=True, help='分数数组的JSON字符串')
    parser.add_argument('--cases', type=str, required=True, help='错误类型数组的JSON字符串')
    
    args = parser.parse_args()
    
    try:
        # 解析JSON字符串
        scores = json.loads(args.scores)
        cases = json.loads(args.cases)
        
        # 生成报告
        report = generate_analysis_report(scores, cases)
        if report:
            print(report, flush=True)  # 添加flush=True确保立即输出
        else:
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)