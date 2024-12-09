import customtkinter as ctk
from openai import OpenAI
from PIL import Image, ImageGrab
from io import BytesIO
import base64
import tkinter as tk  # 导入tkinter
import time

class AIComboApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 设置主题
        self.appearance_mode = "dark"  # 默认暗色主题
        ctk.set_appearance_mode(self.appearance_mode)
        ctk.set_default_color_theme("blue")
        
        self.title("AI Robot By hasakiikii")
        
        # 设置最大化窗口
        self.state('zoomed')
        
        # OpenAI客户端配置 - Gemini
        self.gemini_client = OpenAI(
            base_url="https://yunwu.ai/v1",
            api_key="sk-1vDXSQDYN5NQBckLrw4CU3KSbpeLNQEPcmBvOflTAmelTWO1"
        )
        
        # OpenAI客户端配置 - Claude
        self.claude_client = OpenAI(
            base_url="https://yunwu.ai/v1",
            api_key="sk-Zo48ALYmgM1SSpn8rhuLoJhsKajuZoQ6GUQAS9Ky1b8RuqnH"
        )
        
        # 初始化图片变量
        self.gemini_image_base64 = None
        self.claude_image_base64 = None
        
        # 加载动画变量
        self.loading_animation_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.loading_animation_id = None
        self.is_loading_gemini = False
        self.is_loading_claude = False
        
        # 初始化加载标签
        self.loading_label = None
        
        self.setup_ui()
        self.bind_shortcuts()
    
    def setup_ui(self):
        # 创建主布局
        self.grid_columnconfigure(0, weight=1)  # Gemini区域
        self.grid_columnconfigure(1, weight=1)  # Claude区域
        self.grid_rowconfigure(0, weight=1)  # 聊天区域
        self.grid_rowconfigure(1, weight=0)  # 输入区域
        
        # 创建Gemini和Claude的聊天框架
        self.setup_gemini_frame()
        self.setup_claude_frame()
        
        # 创建统一的输入区域
        self.setup_common_input_frame()
    
    def setup_common_input_frame(self):
        # 统一的输入框架
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # 创建水平布局框架
        horizontal_frame = ctk.CTkFrame(input_frame)
        horizontal_frame.pack(fill="x", padx=10, pady=5)
        
        # 左侧输入文本框
        self.common_input_text = ctk.CTkTextbox(
            horizontal_frame,
            height=100,
            font=("微软雅黑", 12)
        )
        self.common_input_text.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 中间图片显示区域
        image_display_frame = ctk.CTkFrame(horizontal_frame)
        image_display_frame.pack(side="left", fill="y", padx=5)
        
        # 统一的图片显示标签
        self.common_image_label = ctk.CTkLabel(
            image_display_frame,
            text="等待图片...",
            font=("微软雅黑", 12),
            width=200,
            height=100
        )
        self.common_image_label.pack(expand=True)
        
        # 右侧图片操作按钮
        image_buttons_frame = ctk.CTkFrame(horizontal_frame)
        image_buttons_frame.pack(side="left", fill="y")
        
        # 图片操作按钮
        ctk.CTkButton(
            image_buttons_frame,
            text="粘贴图片\n(Ctrl+V)",
            command=self.get_clipboard_image_all,
            width=100,
            height=45,
            fg_color=("#3B8ED0", "#2B5C8F"),  # 深蓝色
            hover_color=("#36719F", "#1E4A7C")
        ).pack(pady=2)
        
        ctk.CTkButton(
            image_buttons_frame,
            text="清除图片",
            command=self.clear_image_all,
            width=100,
            height=45,
            fg_color=("#B85C5C", "#8F2B2B"),  # 深红色
            hover_color=("#A54E4E", "#7C1E1E")
        ).pack(pady=2)
        
        # 发送和清空按钮
        button_frame = ctk.CTkFrame(horizontal_frame)
        button_frame.pack(side="left", fill="y", padx=5)
        
        # 发送按钮
        ctk.CTkButton(
            button_frame,
            text="发送\n(Enter)",
            command=self.send_messages,
            width=100,
            height=45,
            fg_color=("#3B8ED0", "#2B5C8F"),  # 与粘贴图片按钮相同
            hover_color=("#36719F", "#1E4A7C")
        ).pack(pady=2)
        
        # 清空按钮
        ctk.CTkButton(
            button_frame,
            text="清空对话\n(Ctrl+L)",
            command=self.clear_all_chats,
            width=100,
            height=45,
            fg_color=("#B85C5C", "#8F2B2B"),  # 与清除图片按钮相同
            hover_color=("#A54E4E", "#7C1E1E")
        ).pack(pady=2)
        
        # 在主题切换框架之前添加加载动画标签
        self.loading_label = ctk.CTkLabel(
            horizontal_frame,
            text="",  # 初始为空
            font=("微软雅黑", 12),
            width=30
        )
        self.loading_label.pack(side="left", padx=5)
        
        # 主题切换框架和开关
        theme_frame = ctk.CTkFrame(horizontal_frame, fg_color="transparent")
        theme_frame.pack(side="left", fill="y", padx=5)
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="暗色模式",
            command=self.toggle_theme,
            font=("微软雅黑", 12),
            onvalue=True,
            offvalue=False
        )
        self.theme_switch.pack(expand=True, pady=10)
        # 设置初始状态
        if self.appearance_mode == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

    def setup_gemini_frame(self):
        # Gemini主框架
        gemini_frame = ctk.CTkFrame(self)
        gemini_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Gemini标题
        ctk.CTkLabel(
            gemini_frame,
            text="Gemini",
            font=("微软雅黑", 20, "bold")
        ).pack(pady=5)
        
        # 模型选择区域
        model_frame = ctk.CTkFrame(gemini_frame)
        model_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            model_frame,
            text="选择模型:",
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        self.gemini_model_choice = ctk.CTkOptionMenu(
            model_frame,
            values=[
                "gemini-1.5-pro-latest",
                "gemini-1.5-pro-002"
            ],
            font=("微软雅黑", 12)
        )
        self.gemini_model_choice.pack(side="left", padx=5)
        self.gemini_model_choice.set("gemini-1.5-pro-latest")
        
        # 使用tkinter.Text替代CTkTextbox
        self.gemini_chat_history = tk.Text(
            gemini_frame,
            font=("Helvetica", 16),
            wrap="word",
            height=30,
            width=80,
            bg="#2B2B2B",  # 深灰色背景
            fg="white",
            insertbackground="white"
        )
        self.gemini_chat_history.pack(fill="both", expand=True, padx=15, pady=(5, 5))
        
        # 定义文本样式
        self.gemini_chat_history.tag_configure("separator", foreground="#B0C4DE")  # 分隔符颜色
        self.gemini_chat_history.tag_configure("user_prefix", foreground="#ADD8E6", font=("Helvetica", 16))  # "你:" 淡蓝色
        self.gemini_chat_history.tag_configure("ai_prefix", foreground="#FFA07A", font=("Helvetica", 16))  # "Gemini:" 橙色
        self.gemini_chat_history.tag_configure("content", foreground="white", font=("Helvetica", 16))  # 内容为白色
        self.gemini_chat_history.tag_configure("response_time", foreground="#808080", font=("Helvetica", 14))  # 响应时间灰色
        self.gemini_chat_history.tag_configure("error", foreground="#FFB6C1", font=("Helvetica", 16))  # 错误信息淡红色
        
        # 设置初始欢迎消息
        welcome_msg = "欢迎使用 Gemini AI！\n"
        self.gemini_chat_history.insert("end", welcome_msg)

    def setup_claude_frame(self):
        # Claude主框架
        claude_frame = ctk.CTkFrame(self)
        claude_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Claude标题
        ctk.CTkLabel(
            claude_frame,
            text="Claude",
            font=("微软雅黑", 20, "bold")
        ).pack(pady=5)
        
        # 使用tkinter.Text替代CTkTextbox
        self.claude_chat_history = tk.Text(
            claude_frame,
            font=("Helvetica", 16),
            wrap="word",
            height=30,
            width=80,
            bg="#2B2B2B",  # 深灰色背景
            fg="white",
            insertbackground="white"
        )
        self.claude_chat_history.pack(fill="both", expand=True, padx=15, pady=(5, 5))
        
        # 定义文本样式
        self.claude_chat_history.tag_configure("separator", foreground="#B0C4DE")  # 分隔符颜色
        self.claude_chat_history.tag_configure("user_prefix", foreground="#ADD8E6", font=("Helvetica", 16))  # "你:" 淡蓝色
        self.claude_chat_history.tag_configure("ai_prefix", foreground="#FFA07A", font=("Helvetica", 16))  # "Claude:" 橙色
        self.claude_chat_history.tag_configure("content", foreground="white", font=("Helvetica", 16))  # 内容为白色
        self.claude_chat_history.tag_configure("response_time", foreground="#808080", font=("Helvetica", 14))  # 响应时间灰色
        self.claude_chat_history.tag_configure("error", foreground="#FFB6C1", font=("Helvetica", 16))  # 错误信息淡红色
        
        # 设置初始欢迎消息
        welcome_msg = "欢迎使用 Claude AI！\n"
        self.claude_chat_history.insert("end", welcome_msg)

    def bind_shortcuts(self):
        """绑定快捷键"""
        self.bind('<Return>', lambda e: self.send_messages())  # 使用 Enter 键
        self.bind('<Control-l>', lambda e: self.clear_all_chats())
        self.bind('<Control-v>', lambda e: self.get_clipboard_image_all())

    def send_messages(self):
        """同时发送消息给两个AI"""
        user_input = self.common_input_text.get("1.0", "end-1c").strip()
        if not user_input and not (self.gemini_image_base64 or self.claude_image_base64):
            return
        
        # 先发送给Gemini和Claude
        self.send_gemini_message(user_input)
        self.send_claude_message(user_input)
        
        # 等待输出完成后再清空输入框
        self.after(100, lambda: self.common_input_text.delete("1.0", "end"))

    def send_gemini_message(self, user_input):
        """发送Gemini消息"""
        try:
            start_time = time.time()
            self.is_loading_gemini = True
            self._update_loading_animation()
            
            # 先显示用户输入
            self.gemini_chat_history.insert("end", "\n" + "─" * 50 + "\n", "separator")
            self.gemini_chat_history.insert("end", "你: ", "user_prefix")
            self.gemini_chat_history.insert("end", user_input + "\n\n", "content")
            
            # 确保滚动到最新内容
            self.gemini_chat_history.see("end")
            
            # 更新界面
            self.update()
            
            selected_model = self.gemini_model_choice.get()
            messages = [{"role": "user", "content": user_input}]
            
            if self.gemini_image_base64:
                messages[0]["content"] = [
                    {"type": "text", "text": user_input},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{self.gemini_image_base64}"
                        }
                    }
                ]
            
            response = self.gemini_client.chat.completions.create(
                model=selected_model,
                messages=messages
            )
            
            # 停止加载动画
            self.is_loading_gemini = False
            elapsed_time = round(time.time() - start_time)
            
            result = response.choices[0].message.content.replace("*", "")
            
            self.gemini_chat_history.insert("end", f"Gemini ({selected_model}): ", "ai_prefix")
            self.gemini_chat_history.insert("end", f"\n{result}\n", "content")
            self.gemini_chat_history.insert("end", f"\n响应时间: {elapsed_time}秒\n", "response_time")
            
            # 清除图片
            self.clear_image("gemini")
            
            # 确保滚动到最新内容
            self.gemini_chat_history.see("end")
            
        except Exception as e:
            self.is_loading_gemini = False
            self.gemini_chat_history.insert("end", f"\n❌ 错误: {str(e)}\n", "error")
            self.gemini_chat_history.see("end")

    def send_claude_message(self, user_input):
        """发送Claude消息"""
        try:
            start_time = time.time()
            self.is_loading_claude = True
            self._update_loading_animation()
            
            self.claude_chat_history.insert("end", "\n" + "─" * 50 + "\n", "separator")
            self.claude_chat_history.insert("end", "你: ", "user_prefix")
            self.claude_chat_history.insert("end", user_input + "\n\n", "content")
            
            # 确保滚动到最新内容
            self.claude_chat_history.see("end")
            
            messages = []
            if self.claude_image_base64:
                prompt = f"""请分析这张图片并回答以下问题：{user_input}
                
请从以下几个方面进行分析：
1. 图片的主要内容和主题
2. 与问题相关的具体细节
3. 可能的含义或解释
4. 其他值得注意的观察

请用清晰的结构和详细的描述回答。"""

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.claude_image_base64}"
                                }
                            }
                        ]
                    }
                ]
            else:
                messages = [{"role": "user", "content": user_input}]
            
            response = self.claude_client.chat.completions.create(
                model="claude-3-5-sonnet-latest",
                messages=messages
            )
            
            # 停止加载动画
            self.is_loading_claude = False
            elapsed_time = round(time.time() - start_time)
            
            result = response.choices[0].message.content
            self.claude_chat_history.insert("end", "Claude: ", "ai_prefix")
            self.claude_chat_history.insert("end", f"\n{result}\n", "content")
            self.claude_chat_history.insert("end", f"\n响应时间: {elapsed_time}秒\n", "response_time")
            
            # 清除图片
            self.clear_image("claude")
            
            # 确保滚动到最新内容
            self.claude_chat_history.see("end")
            
        except Exception as e:
            self.is_loading_claude = False
            self.claude_chat_history.insert("end", f"\n❌ 错误: {str(e)}\n", "error")
            self.claude_chat_history.see("end")

    def get_clipboard_image_all(self):
        """同时为两个AI获取剪贴板图片"""
        self.get_clipboard_image("gemini")
        self.get_clipboard_image("claude")

    def clear_image_all(self):
        """同时清除两个AI的图片"""
        self.clear_image("gemini")
        self.clear_image("claude")

    def clear_all_chats(self):
        """同时清空两个对话历史"""
        if hasattr(self, 'gemini_chat_history'):
            self.gemini_chat_history.delete("1.0", "end")
            self.gemini_chat_history.insert("end", "欢迎使用 Gemini AI！\n")
        if hasattr(self, 'claude_chat_history'):
            self.claude_chat_history.delete("1.0", "end")
            self.claude_chat_history.insert("end", "欢迎使用 Claude AI！\n")

    def get_clipboard_image(self, client_type):
        """获取剪贴板图片"""
        try:
            image = ImageGrab.grabclipboard()
            if image:
                # 调整图片大小
                display_image = image.copy()
                display_image.thumbnail((200, 100))  # 调整显示大小
                
                # 使用CTkImage显示图片
                photo = ctk.CTkImage(
                    light_image=display_image,
                    dark_image=display_image,
                    size=display_image.size
                )
                
                # 更新统一的图片显示
                self.common_image_label.configure(image=photo, text="")
                self.common_image_label.image = photo
                
                # 处理RGBA图片
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                
                # 转换为base64
                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=95)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                if client_type == "gemini":
                    self.gemini_image_base64 = img_base64
                    self.gemini_chat_history.insert("end", "\n[图片已成功加载]\n")
                    self.gemini_chat_history.see("end")
                else:
                    self.claude_image_base64 = img_base64
                    self.claude_chat_history.insert("end", "\n[图片已成功加载]\n")
                    self.claude_chat_history.see("end")
            else:
                if client_type == "gemini":
                    self.gemini_chat_history.insert("end", "\n剪贴板中没有图片\n")
                    self.gemini_chat_history.see("end")
                else:
                    self.claude_chat_history.insert("end", "\n剪贴板中没有图片\n")
                    self.claude_chat_history.see("end")
        except Exception as e:
            error_msg = f"\n获取图片错误: {str(e)}\n"
            if client_type == "gemini":
                self.gemini_chat_history.insert("end", error_msg)
                self.gemini_chat_history.see("end")
            else:
                self.claude_chat_history.insert("end", error_msg)
                self.claude_chat_history.see("end")

    def clear_image(self, client_type):
        """清除当前图片"""
        if client_type == "gemini":
            self.gemini_image_base64 = None
            self.gemini_chat_history.insert("end", "\n[已清除图片]\n")
        else:
            self.claude_image_base64 = None
            self.claude_chat_history.insert("end", "\n[已清除图片]\n")
        
        # 清除统一的图片显示
        self.common_image_label.configure(image=None, text="等待图片...")

    def toggle_theme(self):
        """切换主题"""
        if self.theme_switch.get():
            self.appearance_mode = "dark"
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="暗色模式")
            
            # 设置深色模式下的对话框背景
            self.gemini_chat_history.configure(bg="#2B2B2B", fg="white", insertbackground="white")
            self.claude_chat_history.configure(bg="#2B2B2B", fg="white", insertbackground="white")
            
            # 设置深色模式下的文本颜色
            self.gemini_chat_history.tag_configure("content", foreground="white")
            self.claude_chat_history.tag_configure("content", foreground="white")
        else:
            self.appearance_mode = "light"
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="亮色模式")
            
            # 设置亮色模式下的对话框背景
            self.gemini_chat_history.configure(bg="white", fg="black", insertbackground="black")
            self.claude_chat_history.configure(bg="white", fg="black", insertbackground="black")
            
            # 设置亮色模式下的文本颜色
            self.gemini_chat_history.tag_configure("content", foreground="black")
            self.claude_chat_history.tag_configure("content", foreground="black")

    def _update_loading_animation(self):
        """更新加载动画"""
        self.current_frame = (self.current_frame + 1) % len(self.loading_animation_frames)
        current_symbol = self.loading_animation_frames[self.current_frame]
        
        if self.is_loading_gemini or self.is_loading_claude:
            self.loading_label.configure(text=current_symbol)
        else:
            self.loading_label.configure(text="")
        
        if self.is_loading_gemini or self.is_loading_claude:
            self.loading_animation_id = self.after(100, self._update_loading_animation)

    def clear_gemini_chat(self):
        """清空Gemini聊天历史"""
        if hasattr(self, 'gemini_chat_history'):
            self.gemini_chat_history.delete("1.0", "end")
            self.gemini_chat_history.insert("end", "欢迎使用 Gemini AI！\n")

    def clear_claude_chat(self):
        """清空Claude聊天历史"""
        if hasattr(self, 'claude_chat_history'):
            self.claude_chat_history.delete("1.0", "end")
            self.claude_chat_history.insert("end", "欢迎使用 Claude AI！\n")

if __name__ == "__main__":
    app = AIComboApp()
    app.mainloop() 