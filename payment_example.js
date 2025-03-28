// Example of how to use the ZaloPay payment methods in the frontend

// Function to fetch available payment methods
async function getPaymentMethods() {
  try {
    const response = await fetch('/api/payments/zalopay/payment-methods');
    const data = await response.json();
    return data.payment_methods;
  } catch (error) {
    console.error('Error fetching payment methods:', error);
    return [];
  }
}

// Function to render payment method options
function renderPaymentMethods(paymentMethods, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';
  
  paymentMethods.forEach(method => {
    const methodElement = document.createElement('div');
    methodElement.className = 'payment-method-option';
    methodElement.dataset.methodId = method.id;
    
    methodElement.innerHTML = `
      <div class="payment-method-radio">
        <input type="radio" name="payment_method" id="method_${method.id}" value="${method.id}">
        <label for="method_${method.id}">
          <img src="${method.icon_url}" alt="${method.name}" class="payment-icon">
          <div class="payment-details">
            <h4>${method.name}</h4>
            <p>${method.description}</p>
          </div>
        </label>
      </div>
    `;
    
    container.appendChild(methodElement);
  });
}

// Function to create a payment
async function createPayment(orderId, userId, cartItems, paymentMethod) {
  try {
    const response = await fetch('/api/payments/zalopay/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}` // Function to get the JWT token
      },
      body: JSON.stringify({
        user_id: userId,
        cart_items: cartItems,
        payment_method: paymentMethod
      })
    });
    
    const data = await response.json();
    
    if (data.order_url) {
      // Redirect to ZaloPay payment page
      window.location.href = data.order_url;
      
      // Alternatively, you can open in a new tab
      // window.open(data.order_url, '_blank');
      
      // Or display QR code for QR payment method
      if (paymentMethod === 'QR') {
        displayQRCode(data.order_url);
      }
      
      // Store app_trans_id for later status check
      localStorage.setItem('app_trans_id', data.app_trans_id);
    }
    
    return data;
  } catch (error) {
    console.error('Error creating payment:', error);
    throw error;
  }
}

// Function to display QR code (requires a QR code library like qrcode.js)
function displayQRCode(orderUrl) {
  const qrContainer = document.getElementById('qr-container');
  if (!qrContainer) return;
  
  // Clear previous content
  qrContainer.innerHTML = '';
  
  // Create QR code (using qrcode.js library)
  // QRCode.toCanvas(qrContainer, orderUrl, function (error) {
  //   if (error) console.error('Error generating QR code:', error);
  // });
  
  // Display instructions
  const instructions = document.createElement('p');
  instructions.textContent = 'Quét mã QR này bằng ứng dụng ZaloPay để thanh toán';
  qrContainer.appendChild(instructions);
}

// Function to check payment status
async function checkPaymentStatus(appTransId) {
  try {
    const response = await fetch(`/api/payments/zalopay/status/${appTransId}`);
    const data = await response.json();
    
    // Handle different status codes
    if (data.return_code === 1) {
      // Payment successful
      showSuccessMessage('Thanh toán thành công!');
      // Redirect to order confirmation page
      window.location.href = '/order-confirmation';
    } else if (data.return_code === 2) {
      // Payment pending
      showInfoMessage('Đang xử lý thanh toán...');
      // Check again after a delay
      setTimeout(() => checkPaymentStatus(appTransId), 5000);
    } else {
      // Payment failed
      showErrorMessage(`Thanh toán thất bại: ${data.return_message}`);
    }
    
    return data;
  } catch (error) {
    console.error('Error checking payment status:', error);
    showErrorMessage('Không thể kiểm tra trạng thái thanh toán');
    throw error;
  }
}

// Example usage
document.addEventListener('DOMContentLoaded', async () => {
  // Fetch and render payment methods
  const paymentMethods = await getPaymentMethods();
  renderPaymentMethods(paymentMethods, 'payment-methods-container');
  
  // Handle payment form submission
  const paymentForm = document.getElementById('payment-form');
  if (paymentForm) {
    paymentForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      
      // Get selected payment method
      const selectedMethod = document.querySelector('input[name="payment_method"]:checked');
      if (!selectedMethod) {
        showErrorMessage('Vui lòng chọn phương thức thanh toán');
        return;
      }
      
      // Get cart items from localStorage or state management
      const cartItems = JSON.parse(localStorage.getItem('cart_items') || '[]');
      if (cartItems.length === 0) {
        showErrorMessage('Giỏ hàng trống');
        return;
      }
      
      // Get user ID from state or localStorage
      const userId = getUserId(); // Implement this function
      
      try {
        // Show loading indicator
        showLoading(true);
        
        // Create payment
        const paymentData = await createPayment(
          null, // Order ID will be created by the backend
          userId,
          cartItems,
          selectedMethod.value
        );
        
        // Hide loading indicator
        showLoading(false);
        
        // Handle payment response
        if (paymentData.order_url) {
          // For QR payment, display QR code
          if (selectedMethod.value === 'QR') {
            displayQRCode(paymentData.order_url);
          } else {
            // For other methods, redirect to ZaloPay
            window.location.href = paymentData.order_url;
          }
        }
      } catch (error) {
        showLoading(false);
        showErrorMessage('Không thể tạo thanh toán');
      }
    });
  }
  
  // Check if returning from ZaloPay
  const appTransId = localStorage.getItem('app_trans_id');
  if (appTransId) {
    // Check payment status
    checkPaymentStatus(appTransId);
    // Clear stored app_trans_id
    localStorage.removeItem('app_trans_id');
  }
});

// Helper functions
function showLoading(isLoading) {
  const loadingElement = document.getElementById('loading-indicator');
  if (loadingElement) {
    loadingElement.style.display = isLoading ? 'block' : 'none';
  }
}

function showSuccessMessage(message) {
  alert(message); // Replace with your UI notification system
}

function showErrorMessage(message) {
  alert(message); // Replace with your UI notification system
}

function showInfoMessage(message) {
  alert(message); // Replace with your UI notification system
}

function getUserId() {
  // Implement this function to get the user ID from your authentication system
  return localStorage.getItem('user_id');
}

function getToken() {
  // Implement this function to get the JWT token from your authentication system
  return localStorage.getItem('token');
} 