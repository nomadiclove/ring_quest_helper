import paddle

# 创建张量
x = paddle.to_tensor([1.0, 2.0, 3.0])
y = paddle.to_tensor([4.0, 5.0, 6.0])

# 执行计算
z = paddle.add(x, y)
print(z)  # 应输出 [5. 7. 9.]

# 验证 GPU 是否可用
print(paddle.is_compiled_with_cuda())  # 应输出 True
print(paddle.device.get_device())      # 应输出 'gpu:0'